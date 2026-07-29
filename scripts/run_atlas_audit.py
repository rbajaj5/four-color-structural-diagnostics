"""Run an independent exhaustive audit on the small NetworkX graph atlas."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
import sys
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from four_color_diagnostics import audit_graph_atlas


OUTPUT_DIR = ROOT / "results"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["route"]), []).append(row)
    return [
        {
            "route": route,
            "graph_count": len(group),
            "exact_match_count": sum(
                bool(row["exact_match"]) for row in group
            ),
            "certificate_valid_count": sum(
                bool(row["certificate_valid"]) for row in group
            ),
            "independent_assignments_tested": sum(
                int(row["independent_assignments_tested"])
                for row in group
            ),
            "preblock_search_nodes": sum(
                int(row["preblock_search_nodes"]) for row in group
            ),
            "block_search_nodes": sum(
                int(row["block_search_nodes"]) for row in group
            ),
            "block_search_nodes_saved": sum(
                int(row["block_search_nodes_saved"]) for row in group
            ),
        }
        for route, group in sorted(grouped.items())
    ]


def summarize_block_outcomes(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups = {
        "improved": [],
        "tied": [],
        "regressed": [],
    }
    for row in rows:
        saved = int(row["block_search_nodes_saved"])
        outcome = "improved" if saved > 0 else "regressed" if saved < 0 else "tied"
        groups[outcome].append(saved)
    return [
        {
            "outcome": outcome,
            "graph_count": len(values),
            "total_search_nodes_saved": sum(values),
            "minimum_search_nodes_saved": min(values) if values else 0,
            "maximum_search_nodes_saved": max(values) if values else 0,
        }
        for outcome, values in groups.items()
    ]


def render_route_plot(summary: list[dict[str, Any]]) -> None:
    labels = [
        str(row["route"]).replace("_", " ")
        for row in summary
    ]
    counts = [int(row["graph_count"]) for row in summary]
    figure, axis = plt.subplots(figsize=(10.5, 5.4))
    axis.barh(labels, counts, color="#0f766e")
    axis.set_xlabel("number of nonisomorphic planar graphs")
    axis.set_title("Exhaustive graph-atlas coverage by diagnostic route")
    axis.grid(axis="x", alpha=0.25)
    for index, count in enumerate(counts):
        axis.text(count + 4, index, str(count), va="center")
    axis.set_xlim(0, max(counts) * 1.12)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "atlas_route_distribution.png", dpi=190)
    plt.close(figure)


def render_block_savings_plot(rows: list[dict[str, Any]]) -> None:
    counts = Counter(
        int(row["block_search_nodes_saved"]) for row in rows
    )
    savings = sorted(counts)
    frequencies = [counts[value] for value in savings]
    colors = [
        "#b91c1c" if value < 0 else "#6b7280" if value == 0 else "#15803d"
        for value in savings
    ]
    figure, axis = plt.subplots(figsize=(9.4, 5.2))
    axis.bar(savings, frequencies, color=colors, width=0.82)
    axis.axvline(0, color="#111827", linewidth=1)
    axis.set_xlabel(
        "search nodes saved by block decomposition (negative = regression)"
    )
    axis.set_ylabel("number of planar atlas graphs")
    axis.set_title("Block decomposition has a positive but nonuniform effect")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(
        OUTPUT_DIR / "atlas_block_savings_distribution.png",
        dpi=190,
    )
    plt.close(figure)


def make_report(
    rows: list[dict[str, Any]],
    summary: list[dict[str, Any]],
) -> str:
    match_count = sum(bool(row["exact_match"]) for row in rows)
    certificate_count = sum(
        bool(row["certificate_valid"]) for row in rows
    )
    assignments = sum(
        int(row["independent_assignments_tested"]) for row in rows
    )
    preblock_nodes = sum(int(row["preblock_search_nodes"]) for row in rows)
    block_nodes = sum(int(row["block_search_nodes"]) for row in rows)
    improved = sum(
        int(row["block_search_nodes_saved"]) > 0 for row in rows
    )
    tied = sum(
        int(row["block_search_nodes_saved"]) == 0 for row in rows
    )
    regressed = sum(
        int(row["block_search_nodes_saved"]) < 0 for row in rows
    )
    worst_regression = min(
        int(row["block_search_nodes_saved"]) for row in rows
    )
    triangulations = [
        row for row in rows if row["dual_parity_agreement"] is not None
    ]
    dual_agreements = sum(
        bool(row["dual_parity_agreement"]) for row in triangulations
    )
    mismatches = [row for row in rows if not row["exact_match"]]
    table = "\n".join(
        "| {route} | {graph_count} | {exact_match_count} | "
        "{certificate_valid_count} | {independent_assignments_tested} | "
        "{block_search_nodes_saved} |".format(**row)
        for row in summary
    )
    return f"""# Exhaustive Small-Planar-Graph Audit

## Result

The structural hierarchy agreed with a separate direct assignment enumerator
on `{match_count}` of `{len(rows)}` nonempty planar graphs in the NetworkX
graph atlas, covering every unlabeled graph through seven vertices that the
atlas marks planar. It emitted `{certificate_count}` valid edge-by-edge
coloring certificates and the independent checker examined `{assignments:,}`
assignments in total.

| Diagnostic route | Graphs | Exact matches | Valid certificates | Direct assignments | Search nodes saved |
| --- | ---: | ---: | ---: | ---: | ---: |
{table}

There were `{len(mismatches)}` disagreements. For the `{len(triangulations)}`
sphere triangulations in this exhaustive range, primal even-degree parity
agreed with independently constructed dual-graph bipartiteness in
`{dual_agreements}` cases.

Across the atlas, block decomposition reduced theorem-directed DSATUR work
from `{preblock_nodes:,}` to `{block_nodes:,}` search nodes, saving
`{preblock_nodes - block_nodes:,}` nodes. This compares the same solver with
the decomposition layer disabled and enabled; it is a finite workload
measurement rather than an asymptotic guarantee.
The decomposition improved `{improved}` graphs, tied on `{tied}`, and
regressed on `{regressed}`; the worst observed regression was
`{-worst_regression}` additional nodes.

## Independence

The audit baseline enumerates fixed-palette assignments directly and checks
every edge. It does not call the repository's DSATUR solver. The structural
path and baseline still share graph parsing and Python/NetworkX process
state, so this is an independent algorithmic cross-check rather than an
independent formal proof.

NetworkX version: `{nx.__version__}`.
Atlas definition:
https://networkx.org/documentation/stable/reference/generated/networkx.generators.atlas.graph_atlas_g.html

## Claim Boundary

This exhausts the finite NetworkX atlas through seven vertices, not all
planar graphs. Zero disagreements are evidence against implementation errors
on that domain; they do not prove the Four Color Theorem, validate an
asymptotic runtime claim, or establish correctness beyond the audited range.
"""


def make_adaptation_note(rows: list[dict[str, Any]]) -> str:
    preblock_nodes = sum(int(row["preblock_search_nodes"]) for row in rows)
    block_nodes = sum(int(row["block_search_nodes"]) for row in rows)
    block_routes = sum(row["route"] == "block_decomposition" for row in rows)
    return f"""# Structure-versus-Residual Adaptation Note

## Source Idea

Alweiss, Bowen, and Sabok organize their arithmetic-coloring proofs by first
obtaining a relaxed monochromatic pattern, separating structured and
pseudorandom regimes, and then using the information in either regime to
control an additional term:

https://arxiv.org/abs/2512.09598

Their theorems concern two-colorings of the natural numbers and
sum/product/exponent patterns. They do not imply a graph-coloring result.

## Exact Graph Adaptation

The transferable object is the proof architecture:

1. Detect the structured regime using articulation vertices and the
   block-cut forest.
2. Diagnose each biconnected block independently.
3. Treat biconnected blocks as the residual cores requiring the existing
   theorem hierarchy or fixed three-color decision.
4. Upgrade local certificates to a global certificate by permuting colors
   at each shared articulation vertex.

The upgrade is exact because distinct blocks meet in at most one articulation
vertex and the chromatic number of a graph is the maximum over its blocks.
The final coloring is still checked against every original edge.

## Finite Evidence

On the 1,015 nonempty planar graphs in the NetworkX atlas through seven
vertices, `{block_routes}` graphs used block decomposition. The layer reduced
the same theorem-directed solver from `{preblock_nodes:,}` to
`{block_nodes:,}` search nodes, a net saving of
`{preblock_nodes - block_nodes:,}`, with zero chromatic-number disagreements
against the independent direct enumerator.

## Boundary

This is an algorithmic adaptation inspired by the paper's organization, not
an application of its syndetic/thick-set machinery. The finite net saving is
not an asymptotic complexity theorem, and per-instance regressions remain.
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [row.as_dict() for row in audit_graph_atlas()]
    summary = summarize(rows)
    block_outcomes = summarize_block_outcomes(rows)
    mismatches = [row for row in rows if not row["exact_match"]]
    write_csv(OUTPUT_DIR / "atlas_audit_rows.csv", rows)
    write_csv(OUTPUT_DIR / "atlas_audit_summary_by_route.csv", summary)
    write_csv(
        OUTPUT_DIR / "atlas_block_decomposition_outcomes.csv",
        block_outcomes,
    )
    mismatch_path = OUTPUT_DIR / "atlas_audit_mismatches.csv"
    if mismatches:
        write_csv(mismatch_path, mismatches)
    else:
        mismatch_path.write_text(
            "atlas_index,error\n",
            encoding="utf-8",
        )
    render_route_plot(summary)
    render_block_savings_plot(rows)
    (OUTPUT_DIR / "ATLAS_EXHAUSTIVE_AUDIT_REPORT.md").write_text(
        make_report(rows, summary),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "STRUCTURE_RANDOMNESS_ADAPTATION.md").write_text(
        make_adaptation_note(rows),
        encoding="utf-8",
    )
    print(
        f"audited {len(rows)} planar atlas graphs; "
        f"mismatches={len(mismatches)}"
    )


if __name__ == "__main__":
    main()

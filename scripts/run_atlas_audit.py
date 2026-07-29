"""Run an independent exhaustive audit on the small NetworkX graph atlas."""

from __future__ import annotations

import csv
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
        }
        for route, group in sorted(grouped.items())
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
    triangulations = [
        row for row in rows if row["dual_parity_agreement"] is not None
    ]
    dual_agreements = sum(
        bool(row["dual_parity_agreement"]) for row in triangulations
    )
    mismatches = [row for row in rows if not row["exact_match"]]
    table = "\n".join(
        "| {route} | {graph_count} | {exact_match_count} | "
        "{certificate_valid_count} | {independent_assignments_tested} |".format(
            **row
        )
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

| Diagnostic route | Graphs | Exact matches | Valid certificates | Direct assignments |
| --- | ---: | ---: | ---: | ---: |
{table}

There were `{len(mismatches)}` disagreements. For the `{len(triangulations)}`
sphere triangulations in this exhaustive range, primal even-degree parity
agreed with independently constructed dual-graph bipartiteness in
`{dual_agreements}` cases.

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


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [row.as_dict() for row in audit_graph_atlas()]
    summary = summarize(rows)
    mismatches = [row for row in rows if not row["exact_match"]]
    write_csv(OUTPUT_DIR / "atlas_audit_rows.csv", rows)
    write_csv(OUTPUT_DIR / "atlas_audit_summary_by_route.csv", summary)
    mismatch_path = OUTPUT_DIR / "atlas_audit_mismatches.csv"
    if mismatches:
        write_csv(mismatch_path, mismatches)
    else:
        mismatch_path.write_text(
            "atlas_index,error\n",
            encoding="utf-8",
        )
    render_route_plot(summary)
    (OUTPUT_DIR / "ATLAS_EXHAUSTIVE_AUDIT_REPORT.md").write_text(
        make_report(rows, summary),
        encoding="utf-8",
    )
    print(
        f"audited {len(rows)} planar atlas graphs; "
        f"mismatches={len(mismatches)}"
    )


if __name__ == "__main__":
    main()

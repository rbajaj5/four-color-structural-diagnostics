"""Run the proof-guided planar coloring benchmark and write artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from four_color_diagnostics import (
    diagnose_planar_graph,
    generic_exact_chromatic,
)
from four_color_diagnostics.fixtures import named_fixtures


OUTPUT_DIR = ROOT / "results"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def render_search_plot(rows: list[dict[str, Any]]) -> None:
    labels = [str(row["fixture_id"]) for row in rows]
    generic = np.array([int(row["generic_search_nodes"]) for row in rows])
    structural = np.array(
        [int(row["structural_search_nodes"]) for row in rows]
    )
    positions = np.arange(len(rows))
    width = 0.38
    figure, axis = plt.subplots(figsize=(11.0, 6.4))
    axis.barh(
        positions - width / 2,
        generic,
        height=width,
        label="blind k=1..4 DSATUR",
        color="#2563eb",
    )
    axis.barh(
        positions + width / 2,
        structural,
        height=width,
        label="theorem-directed search",
        color="#d97706",
    )
    axis.set_yticks(positions, labels)
    axis.set_xscale("symlog", linthresh=1)
    axis.set_xlabel("search nodes (symlog scale)")
    axis.set_title("Structural certificates reduce generic coloring search")
    axis.legend(frameon=False)
    axis.grid(axis="x", alpha=0.25)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "structural_search_comparison.png", dpi=190)
    plt.close(figure)


def make_report(rows: list[dict[str, Any]]) -> str:
    total_generic = sum(int(row["generic_search_nodes"]) for row in rows)
    total_structural = sum(
        int(row["structural_search_nodes"]) for row in rows
    )
    saved = total_generic - total_structural
    route_counts: dict[str, int] = {}
    for row in rows:
        route = str(row["route"])
        route_counts[route] = route_counts.get(route, 0) + 1
    route_lines = "\n".join(
        f"- `{route}`: {count}" for route, count in sorted(route_counts.items())
    )
    one_flip = [
        row
        for row in rows
        if str(row["fixture_id"]).startswith("compactified_one_flip_")
    ]
    one_flip.sort(key=lambda row: int(row["vertex_count"]))
    one_flip_start = one_flip[0]
    one_flip_end = one_flip[-1]
    table = "\n".join(
        "| {fixture_id} | {vertex_count} | {edge_count} | {chromatic_number} | "
        "{route} | {generic_search_nodes} | {structural_search_nodes} | "
        "{search_nodes_saved} |".format(**row)
        for row in rows
    )
    return f"""# Structural Planar Coloring Diagnostic Report

## Result

The executable hierarchy produced valid exact coloring certificates for all
{len(rows)} fixtures. It used `{total_structural}` DSATUR search nodes after
structural preprocessing, compared with `{total_generic}` for blind
increasing-palette search, saving `{saved}` nodes on this finite benchmark.

| Fixture | V | E | chi | Certified route | Generic nodes | Structural nodes | Saved |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
{table}

## Routes

{route_lines}

The compactified checkerboard and one-flip size ladder exercises the exact
Eulerian/non-Eulerian sphere-triangulation transition at `10`, `26`, `50`,
and `82` vertices. On the one-flip branch, parity recognition avoids the
failed 3-color search: measured savings grow from
`{one_flip_start["search_nodes_saved"]}` nodes at
`V={one_flip_start["vertex_count"]}` to
`{one_flip_end["search_nodes_saved"]}` nodes at
`V={one_flip_end["vertex_count"]}`. This is a finite workload observation,
not an asymptotic bound. The other fixtures cover edgeless, bipartite,
triangle-free non-bipartite, and generic planar branches.

## Algorithmic Interpretation

For an arbitrary planar graph that is not settled structurally, exact
chromatic diagnosis requires a fixed 3-color decision. A YES result gives
the remaining three-color case; a NO result combines with Four Color to
give `chi=4`. Or Zamir's 2026 theorem supplies a randomized
`O*((2-epsilon_3)^n)` existence result for the generic fixed-palette
fallback. This repository uses exact DSATUR for small finite certificates;
it does not implement Zamir's algorithm.

## Claim Boundary

This is a proof-guided solver and finite workload comparison. It is not a
new proof of the Four Color Theorem, a new asymptotic coloring algorithm, or
evidence that the measured DSATUR savings persist on arbitrary graph
families. NetworkX supplies planarity recognition; the emitted coloring is
checked directly on every edge.
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    certificates = []
    for fixture_id, graph in named_fixtures():
        diagnosis = diagnose_planar_graph(graph)
        generic_chi, generic, generic_nodes, generic_backtracks = (
            generic_exact_chromatic(graph)
        )
        if generic_chi != diagnosis.chromatic_number:
            raise AssertionError("structural and generic diagnoses disagree")
        row = {
            "fixture_id": fixture_id,
            "vertex_count": graph.vertex_count,
            "edge_count": len(graph.edges),
            "chromatic_number": diagnosis.chromatic_number,
            "route": diagnosis.route,
            "theorem": diagnosis.theorem,
            "triangle_free": diagnosis.triangle_free,
            "sphere_triangulation": diagnosis.sphere_triangulation,
            "all_degrees_even": diagnosis.all_degrees_even,
            "certificate_valid": diagnosis.certificate_valid,
            "generic_search_nodes": generic_nodes,
            "generic_backtracks": generic_backtracks,
            "structural_search_nodes": diagnosis.structural_search_nodes,
            "structural_backtracks": diagnosis.structural_backtracks,
            "search_nodes_saved": (
                generic_nodes - diagnosis.structural_search_nodes
            ),
        }
        rows.append(row)
        certificates.append(
            {
                "fixture_id": fixture_id,
                "chromatic_number": diagnosis.chromatic_number,
                "coloring": list(diagnosis.coloring),
                "edges": [list(edge) for edge in graph.edges],
                "certificate_valid": diagnosis.certificate_valid,
                "generic_certificate_valid": generic.coloring is not None,
            }
        )

    write_csv(OUTPUT_DIR / "structural_benchmark_rows.csv", rows)
    (OUTPUT_DIR / "coloring_certificates.json").write_text(
        json.dumps(certificates, indent=2),
        encoding="utf-8",
    )
    render_search_plot(rows)
    (OUTPUT_DIR / "STRUCTURAL_DIAGNOSTIC_REPORT.md").write_text(
        make_report(rows),
        encoding="utf-8",
    )
    print(f"wrote {len(rows)} exact diagnoses to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

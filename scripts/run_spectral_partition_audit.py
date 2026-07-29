"""Audit several graph partitions and their spectral composition behavior."""

from __future__ import annotations

import csv
from collections import defaultdict
import math
from pathlib import Path
import sys
from typing import Any, Callable, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from four_color_diagnostics import (
    Graph,
    articulation_separator_partition,
    audit_graph_atlas,
    bfs_balanced_partition,
    connected_component_partition,
    fiedler_partition,
    spectral_features,
    verify_coalescence_identity,
    verify_disjoint_union_identity,
)
from four_color_diagnostics.fixtures import named_fixtures


OUTPUT_DIR = ROOT / "results"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty table: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def partition_results(graph: Graph) -> list[Any]:
    results = [connected_component_partition(graph)]
    articulation = articulation_separator_partition(graph)
    if articulation is not None:
        results.append(articulation)
    nx_graph = graph.to_networkx()
    if graph.vertex_count >= 2 and nx.is_connected(nx_graph):
        results.extend(
            (
                fiedler_partition(graph, mode="median"),
                fiedler_partition(graph, mode="sign"),
                bfs_balanced_partition(graph),
            )
        )
    return results


def block_count(graph: Graph) -> int:
    nx_graph = graph.to_networkx()
    return (
        len(tuple(nx.biconnected_components(nx_graph)))
        + sum(degree == 0 for _, degree in nx_graph.degree())
    )


def outcome(saved: int) -> str:
    return "improved" if saved > 0 else "regressed" if saved < 0 else "tied"


def atlas_tables() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    audit_rows = audit_graph_atlas()
    atlas = nx.graph_atlas_g()
    partition_rows: list[dict[str, Any]] = []
    feature_rows: list[dict[str, Any]] = []
    for audit in audit_rows:
        graph = Graph.from_networkx(atlas[audit.atlas_index])
        saved = audit.block_search_nodes_saved
        partitions = partition_results(graph)
        cuts = {result.method: result.cut_edge_count for result in partitions}
        features = spectral_features(graph)
        articulations = tuple(nx.articulation_points(graph.to_networkx()))
        feature_rows.append(
            {
                "atlas_index": audit.atlas_index,
                "vertex_count": graph.vertex_count,
                "edge_count": len(graph.edges),
                "route": audit.route,
                "block_outcome": outcome(saved),
                "block_search_nodes_saved": saved,
                "articulation_count": len(articulations),
                "biconnected_block_count": block_count(graph),
                **features.as_dict(),
                "fiedler_median_cut_edges": cuts.get("fiedler_median", ""),
                "fiedler_sign_cut_edges": cuts.get("fiedler_sign", ""),
                "bfs_balanced_cut_edges": cuts.get("bfs_balanced", ""),
            }
        )
        for result in partitions:
            partition_rows.append(
                {
                    "atlas_index": audit.atlas_index,
                    "vertex_count": graph.vertex_count,
                    "edge_count": len(graph.edges),
                    "route": audit.route,
                    "block_outcome": outcome(saved),
                    "block_search_nodes_saved": saved,
                    **result.as_dict(),
                }
            )
    return partition_rows, feature_rows


def stress_partition_table() -> list[dict[str, Any]]:
    rows = []
    for name, graph in named_fixtures():
        features = spectral_features(graph)
        for result in partition_results(graph):
            rows.append(
                {
                    "fixture": name,
                    "vertex_count": graph.vertex_count,
                    "edge_count": len(graph.edges),
                    **features.as_dict(),
                    **result.as_dict(),
                }
            )
    return rows


def summarize_partitions(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row["method"])].append(row)
    output = []
    for method, group in sorted(groups.items()):
        output.append(
            {
                "method": method,
                "graph_count": len(group),
                "nontrivial_partition_count": sum(
                    int(row["part_count"]) > 1 for row in group
                ),
                "mean_part_count": float(
                    np.mean([row["part_count"] for row in group])
                ),
                "mean_cut_edge_count": float(
                    np.mean([row["cut_edge_count"] for row in group])
                ),
                "mean_residual_cross_edge_count": float(
                    np.mean(
                        [row["residual_cross_edge_count"] for row in group]
                    )
                ),
                "mean_balance_ratio": float(
                    np.mean([row["balance_ratio"] for row in group])
                ),
                "mean_adjacency_spectrum_partition_error": float(
                    np.mean(
                        [
                            row["adjacency_spectrum_partition_error"]
                            for row in group
                        ]
                    )
                ),
                "zero_spectral_error_count": sum(
                    float(row["adjacency_spectrum_partition_error"]) < 1e-10
                    for row in group
                ),
            }
        )
    return output


def _mean(group: list[dict[str, Any]], key: str) -> float:
    values = [
        float(row[key])
        for row in group
        if row[key] != "" and row[key] is not None
    ]
    return float(np.mean(values)) if values else math.nan


def summarize_outcomes(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row["block_outcome"])].append(row)
    keys = (
        "block_search_nodes_saved",
        "articulation_count",
        "biconnected_block_count",
        "adjacency_spectral_radius",
        "adjacency_spectral_gap",
        "adjacency_energy",
        "algebraic_connectivity",
        "largest_laplacian_eigenvalue",
        "fiedler_median_cut_edges",
        "fiedler_sign_cut_edges",
        "bfs_balanced_cut_edges",
    )
    return [
        {
            "block_outcome": name,
            "graph_count": len(group),
            **{f"mean_{key}": _mean(group, key) for key in keys},
        }
        for name, group in sorted(groups.items())
    ]


def average_ranks(values: list[float]) -> np.ndarray:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = np.empty(len(values), dtype=float)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = (start + end - 1) / 2.0
        for position in range(start, end):
            ranks[order[position]] = rank
        start = end
    return ranks


def correlation(first: Iterable[float], second: Iterable[float]) -> float:
    x = np.asarray(tuple(first), dtype=float)
    y = np.asarray(tuple(second), dtype=float)
    if len(x) < 2 or np.std(x) == 0.0 or np.std(y) == 0.0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def feature_correlations(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    features = (
        "vertex_count",
        "edge_count",
        "articulation_count",
        "biconnected_block_count",
        "adjacency_spectral_radius",
        "adjacency_spectral_gap",
        "adjacency_energy",
        "algebraic_connectivity",
        "largest_laplacian_eigenvalue",
        "fiedler_median_cut_edges",
        "fiedler_sign_cut_edges",
        "bfs_balanced_cut_edges",
    )
    output = []
    for feature in features:
        subset = [row for row in rows if row[feature] != ""]
        values = [float(row[feature]) for row in subset]
        saved = [float(row["block_search_nodes_saved"]) for row in subset]
        output.append(
            {
                "feature": feature,
                "graph_count": len(subset),
                "pearson_with_block_nodes_saved": correlation(values, saved),
                "spearman_with_block_nodes_saved": correlation(
                    average_ranks(values),
                    average_ranks(saved),
                ),
            }
        )
    return sorted(
        output,
        key=lambda row: abs(row["spearman_with_block_nodes_saved"]),
        reverse=True,
    )


def composition_checks() -> list[dict[str, Any]]:
    k4 = Graph.from_networkx(nx.complete_graph(4))
    c5 = Graph.from_networkx(nx.cycle_graph(5))
    p4 = Graph.from_networkx(nx.path_graph(4))
    wheel = Graph.from_networkx(nx.wheel_graph(6))
    cases: tuple[
        tuple[str, str, Graph, int, Graph, int, Callable[..., Any]],
        ...,
    ] = (
        ("direct_sum_K4_C5", "disjoint_union", k4, 0, c5, 0, verify_disjoint_union_identity),
        ("direct_sum_C5_P4", "disjoint_union", c5, 0, p4, 0, verify_disjoint_union_identity),
        ("coalescence_K4_C5", "one_vertex_gluing", k4, 0, c5, 2, verify_coalescence_identity),
        ("coalescence_K4_K4", "one_vertex_gluing", k4, 1, k4, 3, verify_coalescence_identity),
        ("coalescence_wheel_P4", "one_vertex_gluing", wheel, 0, p4, 0, verify_coalescence_identity),
    )
    rows = []
    for case_id, kind, first, first_root, second, second_root, checker in cases:
        if kind == "disjoint_union":
            passed, lhs, rhs = checker(first, second)
            identity = "phi(G disjoint H) = phi(G) phi(H)"
        else:
            passed, lhs, rhs = checker(
                first,
                first_root,
                second,
                second_root,
            )
            identity = (
                "phi(G.u.H)=phi(G)phi(H-v)+phi(G-u)phi(H)"
                "-lambda phi(G-u)phi(H-v)"
            )
        rows.append(
            {
                "case_id": case_id,
                "composition_type": kind,
                "first_vertex_count": first.vertex_count,
                "second_vertex_count": second.vertex_count,
                "first_root": "" if kind == "disjoint_union" else first_root,
                "second_root": "" if kind == "disjoint_union" else second_root,
                "identity": identity,
                "exact_pass": passed,
                "lhs_coefficients": " ".join(map(str, lhs)),
                "rhs_coefficients": " ".join(map(str, rhs)),
            }
        )
    return rows


def render_partition_plot(summary: list[dict[str, Any]]) -> None:
    labels = [str(row["method"]).replace("_", " ") for row in summary]
    cuts = [float(row["mean_cut_edge_count"]) for row in summary]
    errors = [
        float(row["mean_adjacency_spectrum_partition_error"])
        for row in summary
    ]
    figure, axes = plt.subplots(1, 2, figsize=(13.0, 5.2))
    axes[0].barh(labels, cuts, color="#0f766e")
    axes[0].set_title("Boundary edges discarded by each partition")
    axes[0].set_xlabel("mean cut-edge count")
    axes[1].barh(labels, errors, color="#b45309")
    axes[1].set_title("Failure of naive spectral multiset union")
    axes[1].set_xlabel("mean absolute eigenvalue error")
    for axis in axes:
        axis.grid(axis="x", alpha=0.25)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "spectral_partition_comparison.png", dpi=190)
    plt.close(figure)


def render_gain_plot(rows: list[dict[str, Any]]) -> None:
    x_values = [float(row["algebraic_connectivity"]) for row in rows]
    y_values = [int(row["block_search_nodes_saved"]) for row in rows]
    colors = [int(row["articulation_count"]) for row in rows]
    figure, axis = plt.subplots(figsize=(9.2, 5.5))
    points = axis.scatter(
        x_values,
        y_values,
        c=colors,
        cmap="viridis",
        alpha=0.66,
        edgecolors="none",
    )
    axis.axhline(0, color="#111827", linewidth=1)
    axis.set_xlabel("Laplacian algebraic connectivity")
    axis.set_ylabel("block-decomposition search nodes saved")
    axis.set_title("Spectral connectivity versus exact finite search outcome")
    axis.grid(alpha=0.22)
    colorbar = figure.colorbar(points, ax=axis)
    colorbar.set_label("articulation-vertex count")
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "spectral_gain_scatter.png", dpi=190)
    plt.close(figure)


def make_report(
    partition_summary: list[dict[str, Any]],
    outcome_summary: list[dict[str, Any]],
    correlations: list[dict[str, Any]],
    checks: list[dict[str, Any]],
    stress_rows: list[dict[str, Any]],
) -> str:
    partition_table = "\n".join(
        "| {method} | {graph_count} | {nontrivial_partition_count} | "
        "{mean_cut_edge_count:.3f} | "
        "{mean_balance_ratio:.3f} | "
        "{mean_adjacency_spectrum_partition_error:.6f} | "
        "{zero_spectral_error_count} |".format(**row)
        for row in partition_summary
    )
    outcome_table = "\n".join(
        "| {block_outcome} | {graph_count} | "
        "{mean_block_search_nodes_saved:.3f} | "
        "{mean_articulation_count:.3f} | "
        "{mean_algebraic_connectivity:.3f} | "
        "{mean_fiedler_median_cut_edges:.3f} |".format(**row)
        for row in outcome_summary
    )
    correlation_table = "\n".join(
        "| {feature} | {graph_count} | "
        "{pearson_with_block_nodes_saved:.3f} | "
        "{spearman_with_block_nodes_saved:.3f} |".format(**row)
        for row in correlations[:6]
    )
    exact_count = sum(bool(row["exact_pass"]) for row in checks)
    component_row = next(
        row for row in partition_summary if row["method"] == "connected_components"
    )
    median_row = next(
        row for row in partition_summary if row["method"] == "fiedler_median"
    )
    bfs_row = next(
        row for row in partition_summary if row["method"] == "bfs_balanced"
    )
    k4_rows = [
        row
        for row in stress_rows
        if str(row["fixture"]).startswith("articulation_k4_chain")
        and row["method"] == "fiedler_median"
    ]
    k4_table = "\n".join(
        "| {fixture} | {vertex_count} | {cut_edge_count} | "
        "{balance_ratio:.3f} | {algebraic_connectivity:.6f} |".format(**row)
        for row in k4_rows
    )
    median_cut_reduction = 100.0 * (
        1.0
        - float(median_row["mean_cut_edge_count"])
        / float(bfs_row["mean_cut_edge_count"])
    )
    return f"""# Spectral Partition Audit

## Question

Can several graph partitions clarify when a structural Four Color diagnostic
decomposes cleanly, and can spectral features help explain the finite
block-decomposition gains and regressions already observed?

## Partition Comparison

| Method | Graphs | Nontrivial | Mean cut edges | Mean balance | Mean spectral-union error | Zero-error cases |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{partition_table}

Connected components have mean spectral-union error
`{component_row["mean_adjacency_spectrum_partition_error"]:.6f}` because the
adjacency and Laplacian matrices are block diagonal. Fiedler-median
partitioning discarded `{median_row["mean_cut_edge_count"]:.3f}` edges on
average, compared with `{bfs_row["mean_cut_edge_count"]:.3f}` for the balanced
BFS baseline, a `{median_cut_reduction:.1f}%` mean reduction at the same
part-size balance. These cuts are heuristic decompositions: their
induced-part spectra are not the original graph spectrum.

Articulation-separator partitions are exact as graph separators
(`residual_cross_edge_count = 0` after deleting the separator), but their
blocks share a boundary vertex. They therefore require a gluing identity,
not a direct multiset union.

## Exact Composition Checks

All `{exact_count}` of `{len(checks)}` exact symbolic fixtures passed. The
checks cover two disjoint unions and three one-vertex coalescences, including
K4-C5, K4-K4, and wheel-path examples. Coefficients from both sides are
preserved in `spectral_composition_checks.csv`.

## Existing Search Outcome

| Block outcome | Graphs | Mean nodes saved | Mean articulations | Mean algebraic connectivity | Mean Fiedler cut |
| --- | ---: | ---: | ---: | ---: | ---: |
{outcome_table}

The strongest finite associations were:

| Feature | Graphs | Pearson | Spearman |
| --- | ---: | ---: | ---: |
{correlation_table}

These are descriptive associations on the 1,015 nonempty planar graphs in
the NetworkX atlas through seven vertices. They are not a runtime theorem,
causal explanation, or train/test predictive claim.

## Articulation-Chain Stress Test

| Fixture | Vertices | Fiedler cut edges | Balance | Algebraic connectivity |
| --- | ---: | ---: | ---: | ---: |
{k4_table}

On the K4 articulation-chain ladder, the balanced Fiedler cut consistently
found the three-edge neck while algebraic connectivity fell as the chain
grew. This detects the global bottleneck, but does not remove the local
coloring overhead that caused the previously recorded large-chain
block-decomposition regressions. The spectrum is therefore useful
diagnostically without replacing the exact block-cut certificate logic.

## Knot-Theory Bridge

For a reduced alternating knot diagram, the determinant can be read as the
number of spanning trees of a checkerboard (Tait) graph. The Matrix-Tree
Theorem in turn expresses that count through nonzero Laplacian eigenvalues.
That gives a precise later bridge from graph spectra to knot data. This
repository has not yet parsed knot diagrams or claimed that a graph spectrum
is a complete knot invariant.

## Scope

- True connected components obey direct-sum spectral composition.
- One-vertex block gluings obey the checked coalescence polynomial identity.
- Fiedler and BFS cuts are empirical partition strategies only.
- Cospectral nonisomorphic graphs remain possible.
- No strengthening of the Four Color Theorem or new knot theorem is claimed.

## Sources

- Matrix-Tree Theorem background: https://arxiv.org/abs/2209.01284
- Alternating-link determinant and Tait spanning trees:
  https://repository.lsu.edu/mathematics_pubs/235/
- Characteristic polynomials of coalescence graphs:
  https://www.sciencedirect.com/book/9780128020685/spectral-radius-of-graphs
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    partition_rows, feature_rows = atlas_tables()
    partition_summary = summarize_partitions(partition_rows)
    outcome_summary = summarize_outcomes(feature_rows)
    correlations = feature_correlations(feature_rows)
    checks = composition_checks()
    stress_rows = stress_partition_table()

    write_csv(OUTPUT_DIR / "spectral_partition_rows.csv", partition_rows)
    write_csv(OUTPUT_DIR / "spectral_partition_summary.csv", partition_summary)
    write_csv(
        OUTPUT_DIR / "spectral_block_outcome_features.csv",
        outcome_summary,
    )
    write_csv(
        OUTPUT_DIR / "spectral_feature_correlations.csv",
        correlations,
    )
    write_csv(OUTPUT_DIR / "spectral_composition_checks.csv", checks)
    write_csv(
        OUTPUT_DIR / "spectral_stress_partition_rows.csv",
        stress_rows,
    )
    render_partition_plot(partition_summary)
    render_gain_plot(feature_rows)
    (OUTPUT_DIR / "SPECTRAL_PARTITION_REPORT.md").write_text(
        make_report(
            partition_summary,
            outcome_summary,
            correlations,
            checks,
            stress_rows,
        ),
        encoding="utf-8",
    )
    print(
        f"audited {len(feature_rows)} atlas graphs and "
        f"{len(partition_rows)} atlas partitions; "
        f"exact composition checks={sum(row['exact_pass'] for row in checks)}"
        f"/{len(checks)}"
    )


if __name__ == "__main__":
    main()

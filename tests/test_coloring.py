from __future__ import annotations

import networkx as nx

from four_color_diagnostics import Graph, solve_k_coloring, verify_coloring


def test_exact_coloring_accepts_and_rejects_k4() -> None:
    graph = Graph.from_networkx(nx.complete_graph(4))
    three = solve_k_coloring(graph, 3)
    four = solve_k_coloring(graph, 4)
    assert not three.feasible
    assert four.feasible
    assert four.coloring is not None
    assert verify_coloring(graph, four.coloring, 4)


def test_fixed_palette_lists_are_enforced() -> None:
    graph = Graph.from_networkx(nx.path_graph(3))
    result = solve_k_coloring(
        graph,
        3,
        allowed={0: {2}, 1: {0, 1}, 2: {2}},
    )
    assert result.feasible
    assert result.coloring is not None
    assert result.coloring[0] == result.coloring[2] == 2
    assert verify_coloring(
        graph,
        result.coloring,
        3,
        allowed={0: {2}, 1: {0, 1}, 2: {2}},
    )

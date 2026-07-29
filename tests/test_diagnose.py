from __future__ import annotations

import networkx as nx
import pytest

from four_color_diagnostics import (
    Graph,
    diagnose_planar_graph,
    generic_exact_chromatic,
)
from four_color_diagnostics.fixtures import (
    checkerboard_diagonals,
    compactified_grid_triangulation,
    flip_diagonal,
    named_fixtures,
)


@pytest.mark.parametrize(
    ("graph", "expected_chi", "expected_route"),
    (
        (
            Graph.from_networkx(nx.path_graph(8)),
            2,
            "bipartite",
        ),
        (
            Graph.from_networkx(nx.cycle_graph(7)),
            3,
            "triangle_free_non_bipartite",
        ),
        (
            Graph.from_networkx(nx.octahedral_graph()),
            3,
            "eulerian_sphere_triangulation",
        ),
        (
            Graph.from_networkx(nx.complete_graph(4)),
            4,
            "non_eulerian_sphere_triangulation",
        ),
        (
            Graph.from_networkx(nx.wheel_graph(6)),
            4,
            "generic_planar_three_color_no",
        ),
    ),
)
def test_structural_routes(
    graph: Graph,
    expected_chi: int,
    expected_route: str,
) -> None:
    diagnosis = diagnose_planar_graph(graph)
    assert diagnosis.chromatic_number == expected_chi
    assert diagnosis.route == expected_route
    assert diagnosis.certificate_valid


def test_compactified_parity_transition() -> None:
    checkerboard = checkerboard_diagonals(4)
    three = compactified_grid_triangulation(checkerboard)
    four = compactified_grid_triangulation(
        flip_diagonal(checkerboard, 1, 1)
    )
    assert diagnose_planar_graph(three).chromatic_number == 3
    assert diagnose_planar_graph(four).chromatic_number == 4


def test_hierarchy_matches_blind_search_on_all_fixtures() -> None:
    for _, graph in named_fixtures():
        diagnosis = diagnose_planar_graph(graph)
        generic_chi, generic, _, _ = generic_exact_chromatic(graph)
        assert diagnosis.chromatic_number == generic_chi
        assert generic.coloring is not None


def test_nonplanar_graph_is_rejected() -> None:
    with pytest.raises(ValueError, match="planar"):
        diagnose_planar_graph(Graph.from_networkx(nx.complete_graph(5)))

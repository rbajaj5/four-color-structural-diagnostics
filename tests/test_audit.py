from __future__ import annotations

import networkx as nx

from four_color_diagnostics import (
    Graph,
    audit_graph_atlas,
    diagnose_planar_graph,
    independent_bruteforce_chromatic,
)
from four_color_diagnostics.fixtures import stacked_triangulation


def test_independent_enumerator_is_not_the_dsatur_path() -> None:
    graph = Graph.from_networkx(nx.wheel_graph(6))
    chromatic_number, coloring, assignments = (
        independent_bruteforce_chromatic(graph)
    )
    assert chromatic_number == 4
    assert len(coloring) == graph.vertex_count
    assert assignments > 0


def test_exhaustive_planar_atlas_audit() -> None:
    rows = audit_graph_atlas()
    assert len(rows) == 1015
    assert all(row.exact_match for row in rows)
    assert all(row.certificate_valid for row in rows)
    assert all(
        row.dual_parity_agreement is not False
        for row in rows
    )


def test_stacked_triangulation_has_dual_parity_certificate() -> None:
    diagnosis = diagnose_planar_graph(stacked_triangulation(24))
    assert diagnosis.sphere_triangulation
    assert diagnosis.chromatic_number == 4
    assert diagnosis.dual_bipartite is False
    assert diagnosis.odd_degree_vertices

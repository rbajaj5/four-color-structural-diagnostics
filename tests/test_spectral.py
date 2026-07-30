from __future__ import annotations

import networkx as nx
import numpy as np

from four_color_diagnostics import (
    Graph,
    articulation_separator_partition,
    bfs_balanced_partition,
    connected_component_partition,
    fiedler_partition,
    verify_coalescence_identity,
    verify_disjoint_union_identity,
)
from four_color_diagnostics.spectral import adjacency_matrix


def test_empty_graph_partition_is_well_defined() -> None:
    result = connected_component_partition(Graph.from_edges(0, ()))
    assert result.parts == ()
    assert result.adjacency_spectrum_partition_error == 0.0


def test_disjoint_union_spectrum_is_multiset_union() -> None:
    first = nx.path_graph(4)
    second = nx.cycle_graph(5)
    union = nx.disjoint_union(first, second)
    expected = np.sort(
        np.concatenate(
            (
                np.linalg.eigvalsh(nx.to_numpy_array(first)),
                np.linalg.eigvalsh(nx.to_numpy_array(second)),
            )
        )
    )
    observed = np.linalg.eigvalsh(
        adjacency_matrix(Graph.from_networkx(union))
    )
    assert np.allclose(observed, expected)
    partition = connected_component_partition(Graph.from_networkx(union))
    assert partition.cut_edge_count == 0
    assert len(partition.parts) == 2
    assert partition.adjacency_spectrum_partition_error < 1e-12
    passed, lhs, rhs = verify_disjoint_union_identity(
        Graph.from_networkx(first),
        Graph.from_networkx(second),
    )
    assert passed
    assert lhs == rhs


def test_coalescence_characteristic_polynomial_identity() -> None:
    first = Graph.from_networkx(nx.complete_graph(4))
    second = Graph.from_networkx(nx.cycle_graph(5))
    passed, lhs, rhs = verify_coalescence_identity(first, 0, second, 2)
    assert passed
    assert lhs == rhs


def test_articulation_partition_is_an_exact_separator() -> None:
    graph = Graph.from_networkx(
        nx.disjoint_union_all((nx.complete_graph(4), nx.complete_graph(4)))
    )
    # Join the two K4 components through a new articulation vertex.
    joined = Graph.from_edges(
        graph.vertex_count + 1,
        (*graph.edges, (3, 8), (4, 8)),
    )
    result = articulation_separator_partition(joined)
    assert result is not None
    assert result.residual_cross_edge_count == 0
    assert len(result.separator_vertices) == 1


def test_fiedler_and_bfs_partitions_cover_without_overlap() -> None:
    graph = Graph.from_networkx(nx.wheel_graph(7))
    results = (
        fiedler_partition(graph, mode="median"),
        fiedler_partition(graph, mode="sign"),
        bfs_balanced_partition(graph),
    )
    for result in results:
        assert set().union(*result.parts) == set(range(graph.vertex_count))
        assert sum(map(len, result.parts)) == graph.vertex_count
        assert result.smallest_part_size > 0

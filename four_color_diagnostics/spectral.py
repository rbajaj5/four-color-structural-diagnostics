"""Spectral diagnostics and deterministic graph partitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .graph import Graph


@dataclass(frozen=True)
class SpectralFeatures:
    vertex_count: int
    connected_component_count: int
    adjacency_spectral_radius: float
    adjacency_spectral_gap: float
    adjacency_energy: float
    algebraic_connectivity: float
    largest_laplacian_eigenvalue: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PartitionResult:
    method: str
    parts: tuple[frozenset[int], ...]
    separator_vertices: tuple[int, ...]
    cut_edge_count: int
    residual_cross_edge_count: int
    smallest_part_size: int
    largest_part_size: int
    balance_ratio: float
    adjacency_spectrum_partition_error: float

    def as_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["part_count"] = len(self.parts)
        row["part_sizes"] = " ".join(
            str(len(part)) for part in self.parts
        )
        row["separator_vertices"] = " ".join(
            str(vertex) for vertex in self.separator_vertices
        )
        del row["parts"]
        return row


def adjacency_matrix(graph: Graph) -> np.ndarray:
    matrix = np.zeros((graph.vertex_count, graph.vertex_count), dtype=float)
    for first, second in graph.edges:
        matrix[first, second] = 1.0
        matrix[second, first] = 1.0
    return matrix


def laplacian_matrix(graph: Graph) -> np.ndarray:
    adjacency = adjacency_matrix(graph)
    return np.diag(adjacency.sum(axis=1)) - adjacency


def spectral_features(graph: Graph) -> SpectralFeatures:
    """Return stable finite-graph adjacency and Laplacian summaries."""

    import networkx as nx

    if graph.vertex_count == 0:
        return SpectralFeatures(0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)
    adjacency_values = np.linalg.eigvalsh(adjacency_matrix(graph))
    laplacian_values = np.linalg.eigvalsh(laplacian_matrix(graph))
    ordered_adjacency = np.sort(adjacency_values)
    spectral_radius = float(np.max(np.abs(adjacency_values)))
    adjacency_gap = (
        float(ordered_adjacency[-1] - ordered_adjacency[-2])
        if graph.vertex_count >= 2
        else 0.0
    )
    algebraic_connectivity = (
        float(max(0.0, laplacian_values[1]))
        if graph.vertex_count >= 2
        else 0.0
    )
    return SpectralFeatures(
        vertex_count=graph.vertex_count,
        connected_component_count=nx.number_connected_components(
            graph.to_networkx()
        ),
        adjacency_spectral_radius=spectral_radius,
        adjacency_spectral_gap=adjacency_gap,
        adjacency_energy=float(np.abs(adjacency_values).sum()),
        algebraic_connectivity=algebraic_connectivity,
        largest_laplacian_eigenvalue=float(laplacian_values[-1]),
    )


def _partition_result(
    graph: Graph,
    method: str,
    parts: tuple[frozenset[int], ...],
    separator_vertices: tuple[int, ...] = (),
) -> PartitionResult:
    if set().union(*parts) != set(range(graph.vertex_count)):
        raise ValueError("partition does not cover every graph vertex")
    if sum(map(len, parts)) != graph.vertex_count:
        raise ValueError("partition parts overlap")
    part_for = {
        vertex: index
        for index, part in enumerate(parts)
        for vertex in part
    }
    separators = set(separator_vertices)
    cut_edges = sum(
        part_for[first] != part_for[second] for first, second in graph.edges
    )
    residual_cross_edges = sum(
        first not in separators
        and second not in separators
        and part_for[first] != part_for[second]
        for first, second in graph.edges
    )
    substantive_sizes = [
        len(part)
        for part in parts
        if not part.issubset(separators)
    ]
    smallest = min(substantive_sizes, default=0)
    largest = max(substantive_sizes, default=0)
    full_spectrum = np.linalg.eigvalsh(adjacency_matrix(graph))
    part_spectrum = (
        np.sort(
            np.concatenate(
                [
                    np.linalg.eigvalsh(
                        adjacency_matrix(induced_subgraph(graph, part))
                    )
                    for part in parts
                ]
            )
        )
        if graph.vertex_count
        else np.asarray([], dtype=float)
    )
    return PartitionResult(
        method=method,
        parts=parts,
        separator_vertices=separator_vertices,
        cut_edge_count=cut_edges,
        residual_cross_edge_count=residual_cross_edges,
        smallest_part_size=smallest,
        largest_part_size=largest,
        balance_ratio=(smallest / largest if largest else 1.0),
        adjacency_spectrum_partition_error=float(
            np.mean(np.abs(np.sort(full_spectrum) - part_spectrum))
            if graph.vertex_count
            else 0.0
        ),
    )


def connected_component_partition(graph: Graph) -> PartitionResult:
    import networkx as nx

    components = tuple(
        sorted(
            (
                frozenset(component)
                for component in nx.connected_components(graph.to_networkx())
            ),
            key=lambda part: (min(part), len(part)),
        )
    )
    return _partition_result(graph, "connected_components", components)


def articulation_separator_partition(
    graph: Graph,
) -> PartitionResult | None:
    """Split at a deterministic articulation vertex when one exists."""

    import networkx as nx

    nx_graph = graph.to_networkx()
    candidates = []
    for vertex in nx.articulation_points(nx_graph):
        residual = nx_graph.copy()
        residual.remove_node(vertex)
        components = tuple(
            frozenset(component)
            for component in nx.connected_components(residual)
        )
        sizes = [len(component) for component in components]
        balance = min(sizes) / max(sizes) if sizes else 1.0
        candidates.append(
            (len(components), balance, -vertex, vertex, components)
        )
    if not candidates:
        return None
    _, _, _, separator, components = max(candidates)
    ordered = tuple(
        sorted(
            components,
            key=lambda part: (min(part), len(part)),
        )
    )
    parts = (*ordered, frozenset((separator,)))
    return _partition_result(
        graph,
        "articulation_separator",
        parts,
        (separator,),
    )


def _fiedler_order(graph: Graph) -> tuple[np.ndarray, np.ndarray]:
    if graph.vertex_count < 2:
        raise ValueError("Fiedler partitions need at least two vertices")
    import networkx as nx

    if not nx.is_connected(graph.to_networkx()):
        raise ValueError("Fiedler partitions require a connected graph")
    eigenvalues, eigenvectors = np.linalg.eigh(laplacian_matrix(graph))
    return eigenvalues, eigenvectors[:, 1]


def fiedler_partition(
    graph: Graph,
    *,
    mode: str = "median",
) -> PartitionResult:
    """Partition a connected graph by its second Laplacian eigenvector."""

    _, vector = _fiedler_order(graph)
    if mode == "median":
        ordered = sorted(
            range(graph.vertex_count),
            key=lambda vertex: (float(vector[vertex]), vertex),
        )
        split = graph.vertex_count // 2
        first = frozenset(ordered[:split])
        second = frozenset(ordered[split:])
    elif mode == "sign":
        first = frozenset(
            vertex
            for vertex, value in enumerate(vector)
            if value < 0.0
        )
        second = frozenset(range(graph.vertex_count)) - first
        if not first or not second:
            return fiedler_partition(graph, mode="median")
    else:
        raise ValueError("mode must be 'median' or 'sign'")
    return _partition_result(
        graph,
        f"fiedler_{mode}",
        (first, second),
    )


def bfs_balanced_partition(graph: Graph) -> PartitionResult:
    """Return a deterministic non-spectral balanced traversal baseline."""

    import networkx as nx

    nx_graph = graph.to_networkx()
    if graph.vertex_count < 2 or not nx.is_connected(nx_graph):
        raise ValueError("balanced BFS requires a connected nontrivial graph")
    start = min(
        range(graph.vertex_count),
        key=lambda vertex: (-graph.degrees[vertex], vertex),
    )
    order = tuple(nx.bfs_tree(nx_graph, start, sort_neighbors=sorted))
    split = graph.vertex_count // 2
    return _partition_result(
        graph,
        "bfs_balanced",
        (frozenset(order[:split]), frozenset(order[split:])),
    )


def delete_vertex(graph: Graph, vertex: int) -> Graph:
    if not 0 <= vertex < graph.vertex_count:
        raise ValueError("vertex is outside the graph")
    remaining = [item for item in range(graph.vertex_count) if item != vertex]
    relabel = {item: index for index, item in enumerate(remaining)}
    return Graph.from_edges(
        graph.vertex_count - 1,
        (
            (relabel[first], relabel[second])
            for first, second in graph.edges
            if first != vertex and second != vertex
        ),
    )


def induced_subgraph(graph: Graph, vertices: frozenset[int]) -> Graph:
    ordered = tuple(sorted(vertices))
    relabel = {vertex: index for index, vertex in enumerate(ordered)}
    return Graph.from_edges(
        len(ordered),
        (
            (relabel[first], relabel[second])
            for first, second in graph.edges
            if first in vertices and second in vertices
        ),
    )


def coalesce_graphs(
    first: Graph,
    first_root: int,
    second: Graph,
    second_root: int,
) -> Graph:
    """Identify one specified vertex from each graph."""

    if not 0 <= first_root < first.vertex_count:
        raise ValueError("first root is outside its graph")
    if not 0 <= second_root < second.vertex_count:
        raise ValueError("second root is outside its graph")
    second_map = {second_root: first_root}
    next_vertex = first.vertex_count
    for vertex in range(second.vertex_count):
        if vertex != second_root:
            second_map[vertex] = next_vertex
            next_vertex += 1
    edges = set(first.edges)
    edges.update(
        tuple(sorted((second_map[u], second_map[v])))
        for u, v in second.edges
    )
    return Graph.from_edges(next_vertex, edges)


def adjacency_characteristic_polynomial(graph: Graph) -> Any:
    """Return the exact adjacency characteristic polynomial over ZZ."""

    import sympy as sp

    variable = sp.Symbol("lambda")
    if graph.vertex_count == 0:
        return sp.Poly(1, variable)
    matrix = sp.zeros(graph.vertex_count)
    for first, second in graph.edges:
        matrix[first, second] = 1
        matrix[second, first] = 1
    return sp.Poly(matrix.charpoly(variable).as_expr(), variable)


def verify_coalescence_identity(
    first: Graph,
    first_root: int,
    second: Graph,
    second_root: int,
) -> tuple[bool, tuple[int, ...], tuple[int, ...]]:
    """Check the exact characteristic-polynomial gluing formula."""

    import sympy as sp

    variable = sp.Symbol("lambda")
    coalesced = coalesce_graphs(first, first_root, second, second_root)
    lhs = adjacency_characteristic_polynomial(coalesced)
    first_poly = adjacency_characteristic_polynomial(first)
    second_poly = adjacency_characteristic_polynomial(second)
    first_deleted = adjacency_characteristic_polynomial(
        delete_vertex(first, first_root)
    )
    second_deleted = adjacency_characteristic_polynomial(
        delete_vertex(second, second_root)
    )
    rhs = sp.Poly(
        first_poly.as_expr() * second_deleted.as_expr()
        + first_deleted.as_expr() * second_poly.as_expr()
        - variable
        * first_deleted.as_expr()
        * second_deleted.as_expr(),
        variable,
    )
    return (
        lhs == rhs,
        tuple(int(value) for value in lhs.all_coeffs()),
        tuple(int(value) for value in rhs.all_coeffs()),
    )


def verify_disjoint_union_identity(
    first: Graph,
    second: Graph,
) -> tuple[bool, tuple[int, ...], tuple[int, ...]]:
    """Check ``phi(G disjoint H) = phi(G) phi(H)`` exactly."""

    import networkx as nx
    import sympy as sp

    variable = sp.Symbol("lambda")
    union = Graph.from_networkx(
        nx.disjoint_union(first.to_networkx(), second.to_networkx())
    )
    lhs = adjacency_characteristic_polynomial(union)
    rhs = sp.Poly(
        adjacency_characteristic_polynomial(first).as_expr()
        * adjacency_characteristic_polynomial(second).as_expr(),
        variable,
    )
    return (
        lhs == rhs,
        tuple(int(value) for value in lhs.all_coeffs()),
        tuple(int(value) for value in rhs.all_coeffs()),
    )

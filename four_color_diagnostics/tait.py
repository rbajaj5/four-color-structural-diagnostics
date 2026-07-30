"""Exact checkerboard Tait graphs and determinant checks from PD codes."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from math import prod
from typing import Iterable

import numpy as np
import sympy as sp


Corner = tuple[int, int]
PDCode = tuple[tuple[int, int, int, int], ...]


@dataclass(frozen=True)
class TaitGraph:
    """A checkerboard multigraph, retaining loops and parallel edges."""

    face_ids: tuple[int, ...]
    edges: tuple[tuple[int, int], ...]

    @property
    def vertex_count(self) -> int:
        return len(self.face_ids)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @property
    def loop_count(self) -> int:
        return sum(first == second for first, second in self.edges)

    @property
    def maximum_edge_multiplicity(self) -> int:
        multiplicities = Counter(
            tuple(sorted((first, second))) for first, second in self.edges
        )
        return max(multiplicities.values(), default=0)

    def laplacian_exact(self) -> sp.Matrix:
        matrix = sp.zeros(self.vertex_count)
        for first, second in self.edges:
            if first == second:
                continue
            matrix[first, first] += 1
            matrix[second, second] += 1
            matrix[first, second] -= 1
            matrix[second, first] -= 1
        return matrix

    def laplacian_spectrum(self) -> tuple[float, ...]:
        matrix = np.asarray(self.laplacian_exact(), dtype=float)
        return tuple(float(value) for value in np.linalg.eigvalsh(matrix))

    def spanning_tree_count(self) -> int:
        """Apply the weighted/multigraph Matrix-Tree Theorem exactly."""

        if self.vertex_count == 0:
            return 0
        if self.vertex_count == 1:
            return 1
        cofactor = self.laplacian_exact()[:-1, :-1]
        return abs(int(cofactor.det()))

    def spectral_spanning_tree_estimate(self) -> float:
        """Use the product of nonzero Laplacian eigenvalues divided by n."""

        if self.vertex_count == 0:
            return 0.0
        nonzero = [
            value
            for value in self.laplacian_spectrum()
            if abs(value) > 1e-9
        ]
        return float(prod(nonzero) / self.vertex_count)


@dataclass(frozen=True)
class TaitPair:
    faces: tuple[tuple[Corner, ...], ...]
    first: TaitGraph
    second: TaitGraph


def normalize_pd_code(code: Iterable[Iterable[int]]) -> PDCode:
    normalized = tuple(tuple(int(value) for value in crossing) for crossing in code)
    if not normalized:
        raise ValueError("a PD code must contain at least one crossing")
    if any(len(crossing) != 4 for crossing in normalized):
        raise ValueError("every PD crossing must contain four arc labels")
    occurrences: dict[int, int] = Counter(
        label for crossing in normalized for label in crossing
    )
    if any(count != 2 for count in occurrences.values()):
        raise ValueError("every PD arc label must occur exactly twice")
    return normalized  # type: ignore[return-value]


def faces_from_pd_code(code: Iterable[Iterable[int]]) -> tuple[tuple[Corner, ...], ...]:
    """Trace complementary regions using Spherogram's corner convention."""

    pd_code = normalize_pd_code(code)
    occurrences: dict[int, list[Corner]] = defaultdict(list)
    for crossing_index, crossing in enumerate(pd_code):
        for strand_index, label in enumerate(crossing):
            occurrences[label].append((crossing_index, strand_index))
    adjacency: dict[Corner, Corner] = {}
    for endpoints in occurrences.values():
        first, second = endpoints
        adjacency[first] = second
        adjacency[second] = first

    unvisited = {
        (crossing, strand)
        for crossing in range(len(pd_code))
        for strand in range(4)
    }
    faces = []
    while unvisited:
        start = min(unvisited)
        face = []
        corner = start
        while True:
            face.append(corner)
            unvisited.remove(corner)
            crossing, strand = corner
            corner = adjacency[(crossing, (strand + 1) % 4)]
            if corner == start:
                break
            if corner not in unvisited:
                raise ValueError("PD face traversal closed inconsistently")
        faces.append(tuple(face))
    return tuple(faces)


def tait_graphs_from_pd_code(code: Iterable[Iterable[int]]) -> TaitPair:
    """Construct both checkerboard multigraphs from a connected PD code."""

    pd_code = normalize_pd_code(code)
    faces = faces_from_pd_code(pd_code)
    face_of = {
        corner: face_index
        for face_index, face in enumerate(faces)
        for corner in face
    }
    opposite_edges = []
    for crossing in range(len(pd_code)):
        opposite_edges.extend(
            (
                (face_of[(crossing, 0)], face_of[(crossing, 2)]),
                (face_of[(crossing, 1)], face_of[(crossing, 3)]),
            )
        )

    import networkx as nx

    checkerboard_union = nx.Graph()
    checkerboard_union.add_nodes_from(range(len(faces)))
    checkerboard_union.add_edges_from(opposite_edges)
    components = tuple(
        sorted(
            (
                tuple(sorted(component))
                for component in nx.connected_components(checkerboard_union)
            ),
            key=lambda component: (component[0], len(component), component),
        )
    )
    if len(components) != 2:
        raise ValueError(
            "a connected checkerboard diagram must yield two region classes"
        )

    graphs = []
    for component in components:
        local = {face: index for index, face in enumerate(component)}
        edges = tuple(
            (local[first], local[second])
            for first, second in opposite_edges
            if first in local and second in local
        )
        if len(edges) != len(pd_code):
            raise AssertionError("each Tait graph needs one edge per crossing")
        graphs.append(TaitGraph(component, edges))
    return TaitPair(faces, graphs[0], graphs[1])


class _DisjointSet:
    def __init__(self, values: Iterable[int]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: int) -> int:
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, first: int, second: int) -> None:
        first_root = self.find(first)
        second_root = self.find(second)
        if first_root != second_root:
            self.parent[max(first_root, second_root)] = min(
                first_root,
                second_root,
            )


def fox_coloring_determinant(code: Iterable[Iterable[int]]) -> int:
    """Compute the knot determinant from the reduced Fox coloring matrix."""

    pd_code = normalize_pd_code(code)
    labels = sorted({label for crossing in pd_code for label in crossing})
    strands = _DisjointSet(labels)
    for _, over_first, _, over_second in pd_code:
        strands.union(over_first, over_second)
    roots = sorted({strands.find(label) for label in labels})
    column = {root: index for index, root in enumerate(roots)}
    matrix = sp.zeros(len(pd_code), len(roots))
    for row, (under_first, over_first, under_second, over_second) in enumerate(
        pd_code
    ):
        for label, coefficient in (
            (under_first, -1),
            (over_first, 1),
            (under_second, -1),
            (over_second, 1),
        ):
            matrix[row, column[strands.find(label)]] += coefficient
    if matrix.rows != matrix.cols:
        raise ValueError("the current Fox gate expects a one-component knot")
    if matrix.rows == 1:
        return 1
    return abs(int(matrix[1:, 1:].det()))

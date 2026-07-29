"""Dependency-light immutable graph representation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


Edge = tuple[int, int]


@dataclass(frozen=True)
class Graph:
    """A finite simple graph on vertices ``range(vertex_count)``."""

    vertex_count: int
    edges: tuple[Edge, ...]

    def __post_init__(self) -> None:
        if self.vertex_count < 0:
            raise ValueError("vertex_count must be nonnegative")
        normalized = set()
        for first, second in self.edges:
            if first == second:
                raise ValueError("loops are not supported")
            if not (0 <= first < self.vertex_count):
                raise ValueError("edge endpoint is outside the vertex set")
            if not (0 <= second < self.vertex_count):
                raise ValueError("edge endpoint is outside the vertex set")
            normalized.add(
                (first, second) if first < second else (second, first)
            )
        object.__setattr__(self, "edges", tuple(sorted(normalized)))

    @classmethod
    def from_edges(
        cls,
        vertex_count: int,
        edges: Iterable[Edge],
    ) -> Graph:
        return cls(vertex_count=vertex_count, edges=tuple(edges))

    @classmethod
    def from_networkx(cls, graph: Any) -> Graph:
        """Relabel a NetworkX graph to consecutive integer vertices."""

        import networkx as nx

        if graph.is_directed() or graph.is_multigraph():
            raise ValueError("only finite simple undirected graphs are supported")
        ordered = sorted(graph.nodes(), key=repr)
        relabel = {vertex: index for index, vertex in enumerate(ordered)}
        relabeled = nx.relabel_nodes(graph, relabel, copy=True)
        return cls.from_edges(relabeled.number_of_nodes(), relabeled.edges())

    @property
    def adjacency(self) -> tuple[frozenset[int], ...]:
        neighbors = [set() for _ in range(self.vertex_count)]
        for first, second in self.edges:
            neighbors[first].add(second)
            neighbors[second].add(first)
        return tuple(frozenset(row) for row in neighbors)

    @property
    def degrees(self) -> tuple[int, ...]:
        return tuple(len(row) for row in self.adjacency)

    def to_networkx(self) -> Any:
        import networkx as nx

        graph = nx.Graph()
        graph.add_nodes_from(range(self.vertex_count))
        graph.add_edges_from(self.edges)
        return graph

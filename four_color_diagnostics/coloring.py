"""Exact finite coloring and certificate validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping, Sequence

from .graph import Graph


@dataclass(frozen=True)
class ColoringResult:
    feasible: bool
    coloring: tuple[int, ...] | None
    search_nodes: int
    backtracks: int
    color_count: int


def verify_coloring(
    graph: Graph,
    coloring: Sequence[int],
    color_count: int,
    allowed: Mapping[int, Collection[int]] | None = None,
) -> bool:
    """Return whether a coloring is a proper fixed-palette certificate."""

    if len(coloring) != graph.vertex_count:
        return False
    if any(color < 0 or color >= color_count for color in coloring):
        return False
    if allowed is not None:
        for vertex, color in enumerate(coloring):
            if color not in allowed.get(vertex, range(color_count)):
                return False
    return all(
        coloring[first] != coloring[second] for first, second in graph.edges
    )


def solve_k_coloring(
    graph: Graph,
    color_count: int,
    allowed: Mapping[int, Collection[int]] | None = None,
) -> ColoringResult:
    """Decide fixed-palette list coloring with exact DSATUR backtracking.

    This is a finite certificate engine, not an implementation of Zamir's
    asymptotic randomized algorithm.
    """

    if color_count < 1:
        raise ValueError("color_count must be positive")
    palette = frozenset(range(color_count))
    domains = []
    for vertex in range(graph.vertex_count):
        domain = (
            palette
            if allowed is None
            else frozenset(allowed.get(vertex, palette))
        )
        if not domain or not domain <= palette:
            raise ValueError("every allowed list must be nonempty and in palette")
        domains.append(domain)

    adjacency = graph.adjacency
    colors = [-1] * graph.vertex_count
    search_nodes = 0
    backtracks = 0

    def choose_vertex() -> int:
        candidates = [
            vertex
            for vertex, color in enumerate(colors)
            if color < 0
        ]
        return max(
            candidates,
            key=lambda vertex: (
                len(
                    {
                        colors[neighbor]
                        for neighbor in adjacency[vertex]
                        if colors[neighbor] >= 0
                    }
                ),
                len(adjacency[vertex]),
                -len(domains[vertex]),
                -vertex,
            ),
        )

    def forward_check(vertex: int) -> bool:
        for neighbor in adjacency[vertex]:
            if colors[neighbor] >= 0:
                continue
            used = {
                colors[other]
                for other in adjacency[neighbor]
                if colors[other] >= 0
            }
            if not (domains[neighbor] - used):
                return False
        return True

    def search(colored_count: int) -> bool:
        nonlocal search_nodes, backtracks
        search_nodes += 1
        if colored_count == graph.vertex_count:
            return True
        vertex = choose_vertex()
        forbidden = {
            colors[neighbor]
            for neighbor in adjacency[vertex]
            if colors[neighbor] >= 0
        }
        candidates = sorted(domains[vertex] - forbidden)
        if colored_count == 0 and allowed is None and candidates:
            candidates = candidates[:1]
        for color in candidates:
            colors[vertex] = color
            if forward_check(vertex) and search(colored_count + 1):
                return True
            colors[vertex] = -1
        backtracks += 1
        return False

    feasible = search(0)
    coloring = tuple(colors) if feasible else None
    if coloring is not None and not verify_coloring(
        graph,
        coloring,
        color_count,
        allowed,
    ):
        raise AssertionError("internal error: invalid coloring certificate")
    return ColoringResult(
        feasible=feasible,
        coloring=coloring,
        search_nodes=search_nodes,
        backtracks=backtracks,
        color_count=color_count,
    )


def bipartite_coloring(graph: Graph) -> tuple[int, ...] | None:
    """Return an exact two-color certificate, or ``None`` for an odd cycle."""

    colors = [-1] * graph.vertex_count
    adjacency = graph.adjacency
    for start in range(graph.vertex_count):
        if colors[start] >= 0:
            continue
        colors[start] = 0
        queue = [start]
        for vertex in queue:
            for neighbor in adjacency[vertex]:
                if colors[neighbor] < 0:
                    colors[neighbor] = 1 - colors[vertex]
                    queue.append(neighbor)
                elif colors[neighbor] == colors[vertex]:
                    return None
    return tuple(colors)

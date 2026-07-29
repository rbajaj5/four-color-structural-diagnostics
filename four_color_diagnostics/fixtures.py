"""Representative exact planar graph fixtures."""

from __future__ import annotations

from typing import Iterable, Sequence

from .graph import Graph


def compactified_grid_triangulation(
    diagonals: Sequence[Sequence[bool]],
) -> Graph:
    """Triangulate a square grid and compactify its boundary by one vertex."""

    if not diagonals or any(len(row) != len(diagonals) for row in diagonals):
        raise ValueError("diagonals must be a nonempty square matrix")
    grid_size = len(diagonals) + 1
    exterior = grid_size * grid_size
    edges = set()

    def add(first: int, second: int) -> None:
        edges.add((first, second) if first < second else (second, first))

    def index(row: int, column: int) -> int:
        return row * grid_size + column

    for row in range(grid_size):
        for column in range(grid_size - 1):
            add(index(row, column), index(row, column + 1))
    for row in range(grid_size - 1):
        for column in range(grid_size):
            add(index(row, column), index(row + 1, column))
    for row in range(grid_size - 1):
        for column in range(grid_size - 1):
            if diagonals[row][column]:
                add(index(row, column), index(row + 1, column + 1))
            else:
                add(index(row + 1, column), index(row, column + 1))
    boundary = (
        [index(0, column) for column in range(grid_size)]
        + [index(row, grid_size - 1) for row in range(1, grid_size)]
        + [
            index(grid_size - 1, column)
            for column in range(grid_size - 2, -1, -1)
        ]
        + [index(row, 0) for row in range(grid_size - 2, 0, -1)]
    )
    for vertex in boundary:
        add(exterior, vertex)
    return Graph.from_edges(exterior + 1, edges)


def checkerboard_diagonals(cell_count: int) -> tuple[tuple[bool, ...], ...]:
    return tuple(
        tuple((row + column) % 2 == 0 for column in range(cell_count))
        for row in range(cell_count)
    )


def flip_diagonal(
    diagonals: Sequence[Sequence[bool]],
    row: int,
    column: int,
) -> tuple[tuple[bool, ...], ...]:
    mutable = [list(values) for values in diagonals]
    mutable[row][column] = not mutable[row][column]
    return tuple(tuple(values) for values in mutable)


def seeded_diagonals(
    cell_count: int,
    seed: int,
) -> tuple[tuple[bool, ...], ...]:
    """Return a reproducible irregular diagonal field."""

    if cell_count < 1:
        raise ValueError("cell_count must be positive")
    state = seed & 0xFFFFFFFF
    rows = []
    for _ in range(cell_count):
        row = []
        for _ in range(cell_count):
            state = (1664525 * state + 1013904223) & 0xFFFFFFFF
            row.append(bool(state & 0x80000000))
        rows.append(tuple(row))
    return tuple(rows)


def stacked_triangulation(vertex_count: int) -> Graph:
    """Build a deterministic stacked sphere triangulation from K4."""

    if vertex_count < 4:
        raise ValueError("a stacked triangulation needs at least four vertices")
    edges = {
        (0, 1),
        (0, 2),
        (0, 3),
        (1, 2),
        (1, 3),
        (2, 3),
    }
    faces = [
        (0, 1, 2),
        (0, 1, 3),
        (0, 2, 3),
        (1, 2, 3),
    ]
    for vertex in range(4, vertex_count):
        face_index = (vertex * 2654435761) % len(faces)
        first, second, third = faces.pop(face_index)
        for neighbor in (first, second, third):
            edges.add(
                (neighbor, vertex)
                if neighbor < vertex
                else (vertex, neighbor)
            )
        faces.extend(
            (
                (first, second, vertex),
                (second, third, vertex),
                (third, first, vertex),
            )
        )
    return Graph.from_edges(vertex_count, edges)


def clique_block_chain(block_count: int, clique_size: int = 4) -> Graph:
    """Join complete planar blocks successively at articulation vertices."""

    if block_count < 1:
        raise ValueError("block_count must be positive")
    if not 2 <= clique_size <= 4:
        raise ValueError("planar clique blocks must have size two through four")
    edges = set()
    articulation = 0
    next_vertex = 1
    for _ in range(block_count):
        block = [articulation] + list(
            range(next_vertex, next_vertex + clique_size - 1)
        )
        for first_index, first in enumerate(block):
            for second in block[first_index + 1 :]:
                edges.add(
                    (first, second) if first < second else (second, first)
                )
        articulation = block[-1]
        next_vertex += clique_size - 1
    return Graph.from_edges(next_vertex, edges)


def stress_fixtures() -> tuple[tuple[str, Graph], ...]:
    fixtures = []
    for cell_count in (4, 6, 8):
        for seed in (7, 19):
            fixtures.append(
                (
                    f"compactified_seeded_{cell_count}_{seed}",
                    compactified_grid_triangulation(
                        seeded_diagonals(cell_count, seed)
                    ),
                )
            )
    for vertex_count in (12, 24, 48):
        fixtures.append(
            (
                f"stacked_triangulation_{vertex_count}",
                stacked_triangulation(vertex_count),
            )
        )
    for block_count in (4, 8, 16):
        fixtures.append(
            (
                f"articulation_k4_chain_{block_count}",
                clique_block_chain(block_count),
            )
        )
    return tuple(fixtures)


def named_fixtures() -> tuple[tuple[str, Graph], ...]:
    import networkx as nx

    fixtures = [
        ("edgeless_8", Graph.from_edges(8, ())),
        ("path_8", Graph.from_networkx(nx.path_graph(8))),
        ("odd_cycle_7", Graph.from_networkx(nx.cycle_graph(7))),
        ("octahedral", Graph.from_networkx(nx.octahedral_graph())),
        ("tetrahedral_K4", Graph.from_networkx(nx.complete_graph(4))),
        ("wheel_6", Graph.from_networkx(nx.wheel_graph(6))),
        ("wheel_7", Graph.from_networkx(nx.wheel_graph(7))),
        ("grid_4x4", Graph.from_networkx(nx.grid_2d_graph(4, 4))),
    ]
    for cell_count in (2, 4, 6, 8):
        checkerboard = checkerboard_diagonals(cell_count)
        fixtures.extend(
            (
                (
                    f"compactified_checkerboard_{cell_count}",
                    compactified_grid_triangulation(checkerboard),
                ),
                (
                    f"compactified_one_flip_{cell_count}",
                    compactified_grid_triangulation(
                        flip_diagonal(
                            checkerboard,
                            cell_count // 2,
                            cell_count // 2,
                        )
                    ),
                ),
            )
        )
    fixtures.extend(stress_fixtures())
    return tuple(fixtures)

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
    return tuple(fixtures)

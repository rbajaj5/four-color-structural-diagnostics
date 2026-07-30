"""Small alternating-knot fixtures for the Tait determinant gate."""

from __future__ import annotations

from dataclasses import dataclass

from .tait import PDCode


@dataclass(frozen=True)
class AlternatingKnotFixture:
    name: str
    pd_code: PDCode
    expected_determinant: int


ALTERNATING_KNOT_FIXTURES = (
    AlternatingKnotFixture(
        "3_1",
        ((5, 2, 0, 3), (3, 0, 4, 1), (1, 4, 2, 5)),
        3,
    ),
    AlternatingKnotFixture(
        "4_1",
        ((7, 4, 0, 5), (3, 0, 4, 1), (1, 7, 2, 6), (5, 3, 6, 2)),
        5,
    ),
    AlternatingKnotFixture(
        "5_1",
        (
            (9, 4, 0, 5),
            (5, 0, 6, 1),
            (1, 6, 2, 7),
            (7, 2, 8, 3),
            (3, 8, 4, 9),
        ),
        5,
    ),
    AlternatingKnotFixture(
        "5_2",
        (
            (4, 0, 5, 9),
            (0, 6, 1, 5),
            (8, 2, 9, 1),
            (2, 8, 3, 7),
            (6, 4, 7, 3),
        ),
        7,
    ),
)

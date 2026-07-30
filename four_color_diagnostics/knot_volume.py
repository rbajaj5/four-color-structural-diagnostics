"""Finite prime-knot fixtures and real-valued geometric volume helpers."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


# Volume of a regular ideal hyperbolic tetrahedron. For a finite-volume
# hyperbolic 3-manifold M, ||M|| = Vol(M) / V3.
REGULAR_IDEAL_TETRAHEDRON_VOLUME = 1.0149416064096536


@dataclass(frozen=True)
class PrimeKnotVolumeFixture:
    name: str
    crossing_count: int
    expected_geometry: str
    torus_type: str


_PRIME_KNOT_COUNTS = {
    3: 1,
    4: 1,
    5: 2,
    6: 3,
    7: 7,
    8: 21,
}

_TORUS_KNOTS = {
    "3_1": "T(2,3)",
    "5_1": "T(2,5)",
    "7_1": "T(2,7)",
    "8_19": "T(3,4)",
}


def prime_knot_volume_fixtures() -> tuple[PrimeKnotVolumeFixture, ...]:
    fixtures = []
    for crossing_count, count in _PRIME_KNOT_COUNTS.items():
        for index in range(1, count + 1):
            name = f"{crossing_count}_{index}"
            torus_type = _TORUS_KNOTS.get(name, "")
            fixtures.append(
                PrimeKnotVolumeFixture(
                    name=name,
                    crossing_count=crossing_count,
                    expected_geometry="torus" if torus_type else "hyperbolic",
                    torus_type=torus_type,
                )
            )
    return tuple(fixtures)


def jsj_hyperbolic_volume(hyperbolic_piece_volumes: Iterable[float]) -> float:
    """Return the additive geometric volume from the hyperbolic JSJ pieces."""

    volumes = tuple(float(value) for value in hyperbolic_piece_volumes)
    if any(value < 0 for value in volumes):
        raise ValueError("hyperbolic piece volumes must be nonnegative")
    return sum(volumes)


def normalized_simplicial_volume(
    hyperbolic_piece_volumes: Iterable[float],
) -> float:
    """Return the numerical Gromov norm from hyperbolic piece volumes."""

    return (
        jsj_hyperbolic_volume(hyperbolic_piece_volumes)
        / REGULAR_IDEAL_TETRAHEDRON_VOLUME
    )


def invariant_collision_rows(
    rows: Iterable[Mapping[str, Any]],
    invariant_key: str,
    volume_key: str,
    tolerance: float = 1e-10,
) -> list[dict[str, Any]]:
    grouped: dict[Any, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row[invariant_key]].append(row)

    collisions = []
    for invariant, members in sorted(grouped.items(), key=lambda item: item[0]):
        if len(members) < 2:
            continue
        volumes = [float(member[volume_key]) for member in members]
        geometries = sorted(
            {str(member["expected_geometry"]) for member in members}
        )
        collisions.append(
            {
                invariant_key: invariant,
                "knot_count": len(members),
                "knot_names": " ".join(
                    str(member["knot_name"]) for member in members
                ),
                "geometry_types": " ".join(geometries),
                "volumes": " ".join(f"{value:.12g}" for value in volumes),
                "minimum_volume": min(volumes),
                "maximum_volume": max(volumes),
                "volume_range": max(volumes) - min(volumes),
                "distinct_volume": max(volumes) - min(volumes) > tolerance,
                "cross_geometry_collision": len(geometries) > 1,
            }
        )
    return collisions

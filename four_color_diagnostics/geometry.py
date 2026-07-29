"""Polygonal-knot geometry helpers for projection stability experiments."""

from __future__ import annotations

from math import gcd
from typing import Iterable, Sequence

import numpy as np


PointArray = np.ndarray


def _closed_polygon(points: Sequence[Sequence[float]] | np.ndarray) -> PointArray:
    polygon = np.asarray(points, dtype=float)
    if polygon.ndim != 2 or polygon.shape[1] != 3:
        raise ValueError("a polygon must have shape (vertex_count, 3)")
    if len(polygon) < 3:
        raise ValueError("a polygon needs at least three vertices")
    if not np.isfinite(polygon).all():
        raise ValueError("polygon coordinates must be finite")
    if np.linalg.norm(polygon[0] - polygon[-1]) < 1e-14:
        polygon = polygon[:-1]
    if len(polygon) < 3:
        raise ValueError("a polygon needs at least three distinct vertices")
    lengths = np.linalg.norm(np.roll(polygon, -1, axis=0) - polygon, axis=1)
    if np.any(lengths < 1e-14):
        raise ValueError("consecutive polygon vertices must be distinct")
    return polygon


def torus_knot_points(
    p: int,
    q: int,
    samples: int,
    *,
    major_radius: float = 2.0,
    minor_radius: float = 1.0,
) -> PointArray:
    """Sample the standard coprime ``T(p, q)`` torus-knot parametrization."""

    if p <= 0 or q <= 0 or gcd(p, q) != 1:
        raise ValueError("p and q must be positive and coprime")
    if samples < 8:
        raise ValueError("at least eight samples are required")
    if major_radius <= minor_radius or minor_radius <= 0:
        raise ValueError("radii must satisfy major_radius > minor_radius > 0")
    parameter = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    radial = major_radius + minor_radius * np.cos(q * parameter)
    return np.column_stack(
        (
            radial * np.cos(p * parameter),
            radial * np.sin(p * parameter),
            minor_radius * np.sin(q * parameter),
        )
    )


def figure_eight_knot_points(samples: int) -> PointArray:
    """Sample a standard smooth figure-eight-knot parametrization."""

    if samples < 8:
        raise ValueError("at least eight samples are required")
    parameter = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    radial = 2.0 + np.cos(2.0 * parameter)
    return np.column_stack(
        (
            radial * np.cos(3.0 * parameter),
            radial * np.sin(3.0 * parameter),
            np.sin(4.0 * parameter),
        )
    )


def subdivide_closed_polygon(
    points: Sequence[Sequence[float]] | np.ndarray,
    factor: int,
) -> PointArray:
    """Subdivide every edge without changing the polygonal image."""

    polygon = _closed_polygon(points)
    if factor < 1:
        raise ValueError("subdivision factor must be positive")
    weights = np.arange(factor, dtype=float) / factor
    refined = []
    for start, end in zip(polygon, np.roll(polygon, -1, axis=0), strict=True):
        refined.extend((1.0 - weight) * start + weight * end for weight in weights)
    return np.asarray(refined)


def projection_frame(
    direction: Sequence[float] | np.ndarray,
) -> tuple[PointArray, PointArray, PointArray]:
    """Return a right-handed frame whose third axis is the viewing direction."""

    view = np.asarray(direction, dtype=float)
    if view.shape != (3,) or not np.isfinite(view).all():
        raise ValueError("projection direction must be a finite 3-vector")
    norm = float(np.linalg.norm(view))
    if norm < 1e-14:
        raise ValueError("projection direction must be nonzero")
    view = view / norm
    helper = (
        np.asarray((0.0, 1.0, 0.0))
        if abs(float(view[1])) < 0.9
        else np.asarray((1.0, 0.0, 0.0))
    )
    horizontal = np.cross(helper, view)
    horizontal /= np.linalg.norm(horizontal)
    vertical = np.cross(view, horizontal)
    return horizontal, vertical, view


def project_along(
    points: Sequence[Sequence[float]] | np.ndarray,
    direction: Sequence[float] | np.ndarray,
) -> PointArray:
    """Express a polygon in a frame where ``direction`` is the depth axis."""

    polygon = _closed_polygon(points)
    horizontal, vertical, view = projection_frame(direction)
    frame = np.column_stack((horizontal, vertical, view))
    return polygon @ frame


def polygon_length(points: Sequence[Sequence[float]] | np.ndarray) -> float:
    polygon = _closed_polygon(points)
    return float(
        np.linalg.norm(np.roll(polygon, -1, axis=0) - polygon, axis=1).sum()
    )


def vertex_distortion_estimate(
    points: Sequence[Sequence[float]] | np.ndarray,
) -> float:
    """Lower-bound knot distortion by checking all vertex pairs."""

    polygon = _closed_polygon(points)
    edge_lengths = np.linalg.norm(
        np.roll(polygon, -1, axis=0) - polygon,
        axis=1,
    )
    cumulative = np.concatenate(([0.0], np.cumsum(edge_lengths)))
    total = float(cumulative[-1])
    maximum = 1.0
    for first in range(len(polygon)):
        for second in range(first + 1, len(polygon)):
            forward = float(cumulative[second] - cumulative[first])
            intrinsic = min(forward, total - forward)
            chord = float(np.linalg.norm(polygon[first] - polygon[second]))
            if chord < 1e-14:
                return float("inf")
            maximum = max(maximum, intrinsic / chord)
    return maximum


def minimum_nonlocal_vertex_clearance(
    points: Sequence[Sequence[float]] | np.ndarray,
    *,
    minimum_arclength_fraction: float = 0.05,
) -> float:
    """Measure clearance between vertices separated along the closed curve."""

    if not 0.0 < minimum_arclength_fraction <= 0.5:
        raise ValueError("minimum_arclength_fraction must lie in (0, 0.5]")
    polygon = _closed_polygon(points)
    edge_lengths = np.linalg.norm(
        np.roll(polygon, -1, axis=0) - polygon,
        axis=1,
    )
    cumulative = np.concatenate(([0.0], np.cumsum(edge_lengths)))
    total = float(cumulative[-1])
    minimum = float("inf")
    for first in range(len(polygon)):
        for second in range(first + 1, len(polygon)):
            forward = float(cumulative[second] - cumulative[first])
            intrinsic = min(forward, total - forward)
            if intrinsic + 1e-14 < minimum_arclength_fraction * total:
                continue
            minimum = min(
                minimum,
                float(np.linalg.norm(polygon[first] - polygon[second])),
            )
    return minimum


def canonical_gauss_signature(
    gauss_rows: Iterable[Sequence[int | float]],
) -> str:
    """Canonicalize a signed Gauss traversal under relabeling and basepoint."""

    rows = tuple(
        (
            int(row[0]),
            int(np.sign(float(row[1]))),
            int(np.sign(float(row[2]))),
        )
        for row in gauss_rows
    )
    if not rows:
        return ""

    def normalize(sequence: tuple[tuple[int, int, int], ...]) -> str:
        labels: dict[int, int] = {}
        tokens = []
        for crossing, over_under, orientation in sequence:
            if crossing not in labels:
                labels[crossing] = len(labels) + 1
            tokens.append(
                f"{labels[crossing]}:{over_under:+d}:{orientation:+d}"
            )
        return "|".join(tokens)

    candidates = []
    for sequence in (rows, tuple(reversed(rows))):
        for offset in range(len(sequence)):
            candidates.append(normalize(sequence[offset:] + sequence[:offset]))
    return min(candidates)


def is_alternating_gauss_traversal(
    gauss_rows: Iterable[Sequence[int | float]],
) -> bool:
    rows = tuple(gauss_rows)
    if not rows:
        return False
    signs = tuple(int(np.sign(float(row[1]))) for row in rows)
    return all(
        signs[index] != signs[(index + 1) % len(signs)]
        for index in range(len(signs))
    )


def crossing_projection_margins(
    projected_points: Sequence[Sequence[float]] | np.ndarray,
    raw_crossings: Iterable[Sequence[float]],
) -> tuple[float, float]:
    """Return minimum crossing angle in degrees and minimum depth separation."""

    polygon = _closed_polygon(projected_points)
    crossings = tuple(tuple(float(value) for value in row) for row in raw_crossings)
    unique = [row for row in crossings if row[0] < row[1]]
    if not unique:
        return float("nan"), float("nan")

    def edge_data(parameter: float) -> tuple[PointArray, PointArray]:
        base = int(np.floor(parameter))
        fraction = parameter - np.floor(parameter)
        index = base % len(polygon)
        next_index = (index + 1) % len(polygon)
        point = (
            (1.0 - fraction) * polygon[index]
            + fraction * polygon[next_index]
        )
        tangent = polygon[next_index] - polygon[index]
        return point, tangent

    angles = []
    depth_separations = []
    for first_parameter, second_parameter, _, _ in unique:
        first_point, first_tangent = edge_data(first_parameter)
        second_point, second_tangent = edge_data(second_parameter)
        first_xy = first_tangent[:2]
        second_xy = second_tangent[:2]
        denominator = float(
            np.linalg.norm(first_xy) * np.linalg.norm(second_xy)
        )
        if denominator < 1e-14:
            angle = 0.0
        else:
            cosine = abs(float(np.dot(first_xy, second_xy))) / denominator
            angle = float(np.degrees(np.arccos(np.clip(cosine, 0.0, 1.0))))
        angles.append(angle)
        depth_separations.append(abs(float(first_point[2] - second_point[2])))
    return min(angles), min(depth_separations)


def crossing_vertex_parameter_margin(
    raw_crossings: Iterable[Sequence[float]],
) -> float:
    """Return the smallest crossing-parameter distance from a polygon vertex."""

    crossings = tuple(tuple(float(value) for value in row) for row in raw_crossings)
    unique = [row for row in crossings if row[0] < row[1]]
    if not unique:
        return float("nan")
    return min(
        abs(parameter - round(parameter))
        for row in unique
        for parameter in row[:2]
    )

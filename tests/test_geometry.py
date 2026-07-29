from __future__ import annotations

import numpy as np
import pytest

from four_color_diagnostics.geometry import (
    canonical_gauss_signature,
    crossing_vertex_parameter_margin,
    figure_eight_knot_points,
    minimum_nonlocal_vertex_clearance,
    polygon_length,
    project_along,
    projection_frame,
    subdivide_closed_polygon,
    torus_knot_points,
    vertex_distortion_estimate,
)


def test_exact_subdivision_preserves_polygon_length_and_old_vertices() -> None:
    polygon = torus_knot_points(2, 3, 24)
    refined = subdivide_closed_polygon(polygon, 4)
    assert refined.shape == (96, 3)
    assert np.allclose(refined[::4], polygon)
    assert polygon_length(refined) == pytest.approx(polygon_length(polygon))


def test_projection_frame_is_orthonormal_and_z_view_preserves_xy() -> None:
    horizontal, vertical, view = projection_frame((0.2, -0.3, 1.0))
    frame = np.column_stack((horizontal, vertical, view))
    assert np.allclose(frame.T @ frame, np.eye(3), atol=1e-12)
    assert np.linalg.det(frame) == pytest.approx(1.0)

    polygon = figure_eight_knot_points(32)
    assert np.allclose(project_along(polygon, (0.0, 0.0, 1.0)), polygon)


def test_geometry_statistics_are_scale_consistent() -> None:
    polygon = torus_knot_points(2, 5, 32)
    assert vertex_distortion_estimate(7.0 * polygon) == pytest.approx(
        vertex_distortion_estimate(polygon)
    )
    assert minimum_nonlocal_vertex_clearance(7.0 * polygon) == pytest.approx(
        7.0 * minimum_nonlocal_vertex_clearance(polygon)
    )


def test_gauss_signature_ignores_labels_basepoint_and_orientation() -> None:
    rows = (
        (8, 1, -1),
        (3, -1, 1),
        (8, -1, -1),
        (3, 1, 1),
    )
    shifted_and_relabelled = (
        (40, -1, -1),
        (90, 1, 1),
        (40, 1, -1),
        (90, -1, 1),
    )
    reversed_rows = tuple(reversed(rows))
    expected = canonical_gauss_signature(rows)
    assert canonical_gauss_signature(shifted_and_relabelled) == expected
    assert canonical_gauss_signature(reversed_rows) == expected


def test_crossing_vertex_parameter_margin_detects_endpoint_degeneracy() -> None:
    raw = (
        (2.0, 8.25, 1.0, -1.0),
        (8.25, 2.0, -1.0, -1.0),
    )
    assert crossing_vertex_parameter_margin(raw) == 0.0

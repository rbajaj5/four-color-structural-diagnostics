from __future__ import annotations

import pytest

from four_color_diagnostics.knot_volume import (
    REGULAR_IDEAL_TETRAHEDRON_VOLUME,
    invariant_collision_rows,
    jsj_hyperbolic_volume,
    normalized_simplicial_volume,
    prime_knot_volume_fixtures,
)


def test_prime_fixture_registry_through_eight_crossings() -> None:
    fixtures = prime_knot_volume_fixtures()
    assert len(fixtures) == 35
    assert len({fixture.name for fixture in fixtures}) == 35
    torus_names = {
        fixture.name
        for fixture in fixtures
        if fixture.expected_geometry == "torus"
    }
    assert torus_names == {"3_1", "5_1", "7_1", "8_19"}


def test_jsj_volume_is_additive_and_nonnegative() -> None:
    assert jsj_hyperbolic_volume(()) == 0.0
    assert jsj_hyperbolic_volume((2.0, 3.5)) == 5.5
    assert normalized_simplicial_volume(
        (REGULAR_IDEAL_TETRAHEDRON_VOLUME,)
    ) == pytest.approx(1.0)
    with pytest.raises(ValueError, match="nonnegative"):
        jsj_hyperbolic_volume((2.0, -1.0))


def test_invariant_collisions_preserve_volume_distinctions() -> None:
    rows = [
        {
            "knot_name": "4_1",
            "fox_determinant": 5,
            "expected_geometry": "hyperbolic",
            "volume": 2.029883,
        },
        {
            "knot_name": "5_1",
            "fox_determinant": 5,
            "expected_geometry": "torus",
            "volume": 0.0,
        },
        {
            "knot_name": "3_1",
            "fox_determinant": 3,
            "expected_geometry": "torus",
            "volume": 0.0,
        },
    ]
    collisions = invariant_collision_rows(
        rows,
        invariant_key="fox_determinant",
        volume_key="volume",
    )
    assert len(collisions) == 1
    assert collisions[0]["fox_determinant"] == 5
    assert collisions[0]["distinct_volume"] is True
    assert collisions[0]["cross_geometry_collision"] is True

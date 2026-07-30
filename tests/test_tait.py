from __future__ import annotations

import pytest

from four_color_diagnostics.tait import (
    faces_from_pd_code,
    fox_coloring_determinant,
    tait_graphs_from_pd_code,
)
from four_color_diagnostics.tait_fixtures import (
    ALTERNATING_KNOT_FIXTURES,
    AlternatingKnotFixture,
)


@pytest.mark.parametrize("fixture", ALTERNATING_KNOT_FIXTURES)
def test_tait_and_fox_determinants_agree(
    fixture: AlternatingKnotFixture,
) -> None:
    pair = tait_graphs_from_pd_code(fixture.pd_code)
    assert len(pair.faces) == len(fixture.pd_code) + 2
    assert pair.first.spanning_tree_count() == fixture.expected_determinant
    assert pair.second.spanning_tree_count() == fixture.expected_determinant
    assert (
        fox_coloring_determinant(fixture.pd_code)
        == fixture.expected_determinant
    )
    assert pair.first.spectral_spanning_tree_estimate() == pytest.approx(
        fixture.expected_determinant
    )
    assert pair.second.spectral_spanning_tree_estimate() == pytest.approx(
        fixture.expected_determinant
    )


def test_invalid_pd_code_is_rejected() -> None:
    with pytest.raises(ValueError, match="exactly twice"):
        faces_from_pd_code(((0, 1, 2, 3),))


def test_determinant_is_stable_under_pd_relabeling_and_reordering() -> None:
    fixture = ALTERNATING_KNOT_FIXTURES[-1]
    labels = sorted(
        {label for crossing in fixture.pd_code for label in crossing}
    )
    relabel = {
        label: 100 + 7 * index for index, label in enumerate(reversed(labels))
    }
    transformed = tuple(
        tuple(relabel[label] for label in (*crossing[2:], *crossing[:2]))
        for crossing in reversed(fixture.pd_code)
    )
    pair = tait_graphs_from_pd_code(transformed)
    assert pair.first.spanning_tree_count() == fixture.expected_determinant
    assert pair.second.spanning_tree_count() == fixture.expected_determinant
    assert fox_coloring_determinant(transformed) == fixture.expected_determinant

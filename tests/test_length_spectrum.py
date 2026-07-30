from __future__ import annotations

import math

import numpy as np
import pytest

from four_color_diagnostics.length_spectrum import (
    ShortGeodesic,
    leave_one_out_ridge_predictions,
    paired_sign_test_summary,
    prediction_error_metrics,
    principal_angle,
    short_spectrum_distance,
    short_spectrum_fingerprint,
    summarize_short_spectrum,
)


def fixture_spectrum() -> tuple[ShortGeodesic, ...]:
    return (
        ShortGeodesic(1.0, -0.5, 2),
        ShortGeodesic(1.5, 1.0, 1),
        ShortGeodesic(2.0, -2.0, 3),
        ShortGeodesic(2.25, 2.5, 1),
        ShortGeodesic(2.4, -3.0, 2),
    )


def test_principal_angle_is_orientation_independent() -> None:
    assert principal_angle(-0.5) == pytest.approx(0.5)
    assert principal_angle(2.0 * math.pi - 0.5) == pytest.approx(0.5)
    assert principal_angle(math.pi) == pytest.approx(math.pi)


def test_short_spectrum_summary_respects_multiplicity() -> None:
    summary = summarize_short_spectrum(fixture_spectrum())
    assert summary["length_spectrum_record_count"] == 5
    assert summary["length_spectrum_multiplicity_count"] == 9
    assert summary["geodesic_count_le_1_5"] == 3
    assert summary["geodesic_count_le_2_0"] == 6
    assert summary["geodesic_count_le_2_5"] == 9
    assert summary["systole_numeric"] == pytest.approx(1.0)
    assert summary["second_to_first_length_ratio"] == pytest.approx(1.5)
    assert 0.0 <= summary["twist_angle_entropy_8bin"] <= 1.0
    assert 0.0 <= summary["twist_angle_resultant"] <= 1.0


def test_fingerprint_and_distance_ignore_scale_and_orientation() -> None:
    first = fixture_spectrum()
    second = tuple(
        ShortGeodesic(
            3.0 * record.real_length,
            -record.twist_angle,
            record.multiplicity,
        )
        for record in first
    )
    assert short_spectrum_fingerprint(first) == short_spectrum_fingerprint(
        second
    )
    assert short_spectrum_distance(first, second) == pytest.approx(0.0)


def test_leave_one_out_ridge_predictions_are_finite() -> None:
    x = np.asarray([[value, value**2] for value in range(1, 7)], dtype=float)
    y = np.asarray([2.0 * value + 1.0 for value in range(1, 7)], dtype=float)
    predicted = leave_one_out_ridge_predictions(x, y, alpha=0.1)
    metrics = prediction_error_metrics(y, predicted)
    assert np.all(np.isfinite(predicted))
    assert metrics["rmse"] < 1.0
    assert metrics["mae"] < 1.0


def test_invalid_spectrum_is_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        summarize_short_spectrum(
            (
                ShortGeodesic(0.0, 0.0),
                ShortGeodesic(1.0, 0.0),
            )
        )


def test_paired_sign_test_is_exact_and_drops_ties() -> None:
    summary = paired_sign_test_summary(
        baseline_errors=(2.0, 2.0, 2.0, 2.0, 1.0),
        candidate_errors=(1.0, 1.0, 1.0, 1.0, 1.0),
    )
    assert summary["improved_row_count"] == 4
    assert summary["paired_non_tie_count"] == 4
    assert summary["sign_test_pvalue_two_sided"] == pytest.approx(0.125)

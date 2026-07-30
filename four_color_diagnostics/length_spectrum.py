"""Finite complex-length statistics for hyperbolic knot diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class ShortGeodesic:
    """One grouped oriented-geodesic record from a length-spectrum backend."""

    real_length: float
    twist_angle: float
    multiplicity: int = 1


def principal_angle(angle: float) -> float:
    """Return an angle in the orientation-independent interval [0, pi]."""

    wrapped = (float(angle) + math.pi) % (2.0 * math.pi) - math.pi
    return abs(wrapped)


def _validate_geodesics(
    geodesics: Iterable[ShortGeodesic],
) -> tuple[ShortGeodesic, ...]:
    records = tuple(geodesics)
    if not records:
        raise ValueError("at least one short geodesic is required")
    for record in records:
        if not math.isfinite(record.real_length) or record.real_length <= 0.0:
            raise ValueError("real geodesic lengths must be finite and positive")
        if not math.isfinite(record.twist_angle):
            raise ValueError("twist angles must be finite")
        if record.multiplicity < 1:
            raise ValueError("multiplicities must be positive integers")
    return tuple(
        sorted(
            records,
            key=lambda item: (
                item.real_length,
                principal_angle(item.twist_angle),
                item.multiplicity,
            ),
        )
    )


def short_spectrum_fingerprint(
    geodesics: Iterable[ShortGeodesic],
    record_count: int = 5,
    digits: int = 8,
) -> str:
    """Return a scale-free, orientation-independent finite fingerprint."""

    records = _validate_geodesics(geodesics)
    if record_count < 1:
        raise ValueError("record_count must be positive")
    systole = records[0].real_length
    pieces = []
    for record in records[:record_count]:
        pieces.append(
            "{length:.{digits}f}:{twist:.{digits}f}:{multiplicity}".format(
                length=record.real_length / systole,
                twist=principal_angle(record.twist_angle),
                multiplicity=record.multiplicity,
                digits=digits,
            )
        )
    return "|".join(pieces)


def short_spectrum_distance(
    first: Iterable[ShortGeodesic],
    second: Iterable[ShortGeodesic],
    record_count: int = 5,
) -> float:
    """Compare scale-free short spectra using length, twist cosine, and mass."""

    a = _validate_geodesics(first)
    b = _validate_geodesics(second)
    if len(a) < record_count or len(b) < record_count:
        raise ValueError("both spectra must contain record_count records")
    if record_count < 1:
        raise ValueError("record_count must be positive")

    def vector(
        records: tuple[ShortGeodesic, ...],
    ) -> np.ndarray:
        systole = records[0].real_length
        maximum_multiplicity = max(
            record.multiplicity for record in records[:record_count]
        )
        values = []
        for record in records[:record_count]:
            values.extend(
                (
                    record.real_length / systole,
                    math.cos(record.twist_angle),
                    record.multiplicity / maximum_multiplicity,
                )
            )
        return np.asarray(values, dtype=float)

    return float(np.linalg.norm(vector(a) - vector(b)))


def summarize_short_spectrum(
    geodesics: Iterable[ShortGeodesic],
    cutoffs: Sequence[float] = (1.5, 2.0, 2.5),
    angular_bins: int = 8,
) -> dict[str, float | int | str]:
    """Compute finite scale-free and angular statistics.

    The count-growth slope is only a finite-cutoff entropy proxy. It is not
    the topological entropy of a geodesic flow.
    """

    records = _validate_geodesics(geodesics)
    if len(records) < 2:
        raise ValueError("at least two distinct spectrum records are required")
    if angular_bins < 2:
        raise ValueError("angular_bins must be at least two")
    cutoff_values = tuple(float(value) for value in cutoffs)
    if (
        len(cutoff_values) < 2
        or any(value <= 0.0 for value in cutoff_values)
        or any(
            first >= second
            for first, second in zip(cutoff_values, cutoff_values[1:])
        )
    ):
        raise ValueError("cutoffs must be positive and strictly increasing")

    expanded_lengths = np.asarray(
        [
            record.real_length
            for record in records
            for _ in range(record.multiplicity)
        ],
        dtype=float,
    )
    expanded_angles = np.asarray(
        [
            principal_angle(record.twist_angle)
            for record in records
            for _ in range(record.multiplicity)
        ],
        dtype=float,
    )
    counts = np.asarray(
        [
            sum(
                record.multiplicity
                for record in records
                if record.real_length <= cutoff + 1e-12
            )
            for cutoff in cutoff_values
        ],
        dtype=float,
    )
    design = np.column_stack(
        (np.ones(len(cutoff_values)), np.asarray(cutoff_values, dtype=float))
    )
    entropy_slope = float(
        np.linalg.lstsq(design, np.log1p(counts), rcond=None)[0][1]
    )

    angle_counts, _ = np.histogram(
        expanded_angles,
        bins=angular_bins,
        range=(0.0, math.pi),
    )
    probabilities = angle_counts / float(np.sum(angle_counts))
    positive_probabilities = probabilities[probabilities > 0.0]
    angle_entropy = float(
        -np.sum(positive_probabilities * np.log(positive_probabilities))
        / math.log(angular_bins)
    )
    angle_resultant = float(
        abs(np.mean(np.exp(1j * expanded_angles)))
    )

    mean_length = float(np.mean(expanded_lengths))
    standard_deviation = float(np.std(expanded_lengths))
    output: dict[str, float | int | str] = {
        "length_spectrum_record_count": len(records),
        "length_spectrum_multiplicity_count": len(expanded_lengths),
        "systole_numeric": records[0].real_length,
        "second_to_first_length_ratio": (
            records[1].real_length / records[0].real_length
        ),
        "mean_short_length": mean_length,
        "short_length_standard_deviation": standard_deviation,
        "short_length_cv": standard_deviation / mean_length,
        "finite_counting_entropy_proxy": entropy_slope,
        "twist_angle_entropy_8bin": angle_entropy,
        "twist_angle_resultant": angle_resultant,
        "twist_angle_max_sector_fraction": float(np.max(probabilities)),
        "short_spectrum_fingerprint": short_spectrum_fingerprint(records),
    }
    for cutoff, count in zip(cutoff_values, counts, strict=True):
        label = str(cutoff).replace(".", "_")
        output[f"geodesic_count_le_{label}"] = int(count)
    return output


def leave_one_out_ridge_predictions(
    features: Sequence[Sequence[float]],
    target: Sequence[float],
    alpha: float = 1.0,
) -> np.ndarray:
    """Return fixed-alpha LOOCV ridge predictions with fold-local scaling."""

    x = np.asarray(features, dtype=float)
    y = np.asarray(target, dtype=float)
    if x.ndim != 2 or y.ndim != 1 or x.shape[0] != y.shape[0]:
        raise ValueError("features and target have incompatible shapes")
    if x.shape[0] < 3:
        raise ValueError("at least three observations are required")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("features and target must be finite")
    if alpha < 0.0:
        raise ValueError("alpha must be nonnegative")

    predictions = np.empty_like(y)
    for holdout in range(len(y)):
        mask = np.ones(len(y), dtype=bool)
        mask[holdout] = False
        train_x = x[mask]
        train_y = y[mask]
        means = np.mean(train_x, axis=0)
        scales = np.std(train_x, axis=0)
        scales[scales == 0.0] = 1.0
        standardized = (train_x - means) / scales
        centered_y = train_y - np.mean(train_y)
        gram = standardized.T @ standardized
        coefficients = np.linalg.solve(
            gram + alpha * np.eye(x.shape[1]),
            standardized.T @ centered_y,
        )
        predictions[holdout] = (
            np.mean(train_y)
            + ((x[holdout] - means) / scales) @ coefficients
        )
    return predictions


def prediction_error_metrics(
    observed: Sequence[float],
    predicted: Sequence[float],
) -> dict[str, float]:
    """Return RMSE and MAE for paired finite predictions."""

    y = np.asarray(observed, dtype=float)
    y_hat = np.asarray(predicted, dtype=float)
    if y.shape != y_hat.shape or y.ndim != 1:
        raise ValueError("observed and predicted must be paired vectors")
    residual = y_hat - y
    return {
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "mae": float(np.mean(np.abs(residual))),
    }


def paired_sign_test_summary(
    baseline_errors: Sequence[float],
    candidate_errors: Sequence[float],
    tolerance: float = 1e-12,
) -> dict[str, float | int]:
    """Return an exact two-sided sign test for paired error improvements."""

    baseline = np.asarray(baseline_errors, dtype=float)
    candidate = np.asarray(candidate_errors, dtype=float)
    if baseline.shape != candidate.shape or baseline.ndim != 1:
        raise ValueError("baseline and candidate errors must be paired vectors")
    if tolerance < 0.0:
        raise ValueError("tolerance must be nonnegative")
    differences = baseline - candidate
    non_ties = differences[np.abs(differences) > tolerance]
    sample_size = len(non_ties)
    improved = int(np.sum(non_ties > 0.0))
    if sample_size == 0:
        p_value = 1.0
    elif improved <= sample_size / 2.0:
        tail = sum(
            math.comb(sample_size, count)
            for count in range(improved + 1)
        ) / (2**sample_size)
        p_value = min(1.0, 2.0 * tail)
    else:
        tail = sum(
            math.comb(sample_size, count)
            for count in range(improved, sample_size + 1)
        ) / (2**sample_size)
        p_value = min(1.0, 2.0 * tail)
    return {
        "improved_row_count": improved,
        "paired_non_tie_count": sample_size,
        "sign_test_pvalue_two_sided": p_value,
    }

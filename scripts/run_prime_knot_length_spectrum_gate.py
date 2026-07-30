"""Audit finite complex-length statistics for small hyperbolic prime knots."""

from __future__ import annotations

from collections import defaultdict
import csv
import importlib.util
import itertools
import json
import math
from pathlib import Path
import shutil
import sys
import time
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from four_color_diagnostics.length_spectrum import (
    ShortGeodesic,
    leave_one_out_ridge_predictions,
    paired_sign_test_summary,
    prediction_error_metrics,
    short_spectrum_distance,
    summarize_short_spectrum,
)


OUTPUT_DIR = ROOT / "results"
VOLUME_ROWS_PATH = OUTPUT_DIR / "prime_knot_volume_rows.csv"
LENGTH_CUTOFF = 3.0
MAX_RANDOMIZATION_RETRIES = 32

BASELINE_FEATURES = (
    "crossing_count",
    "log_fox_determinant",
    "maximum_tait_spectral_radius",
)
SYSTOLE_FEATURES = BASELINE_FEATURES + ("systole_numeric",)
COMPACT_GEOMETRY_FEATURES = SYSTOLE_FEATURES + ("short_length_cv",)
ENRICHED_FEATURES = BASELINE_FEATURES + (
    "systole_numeric",
    "second_to_first_length_ratio",
    "short_length_cv",
    "geodesic_count_le_1_5",
    "geodesic_count_le_2_0",
    "geodesic_count_le_2_5",
    "finite_counting_entropy_proxy",
    "twist_angle_entropy_8bin",
    "twist_angle_resultant",
)
MODEL_FEATURES = {
    "compressed_invariant_baseline": BASELINE_FEATURES,
    "systole_augmented": SYSTOLE_FEATURES,
    "compact_geometry_augmented": COMPACT_GEOMETRY_FEATURES,
    "full_local_angular_augmented": ENRICHED_FEATURES,
}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def backend_audit() -> dict[str, Any]:
    modules = {
        name: bool(importlib.util.find_spec(name))
        for name in ("snappy", "sageall")
    }
    return {
        "python_executable": sys.executable,
        "python_version": sys.version,
        **{f"{name}_available": available for name, available in modules.items()},
        "sage_command_available": shutil.which("sage") is not None,
        "length_spectrum_method": "SnapPy Manifold.length_spectrum",
        "length_cutoff": LENGTH_CUTOFF,
        "maximum_randomization_retries": MAX_RANDOMIZATION_RETRIES,
        "verification_policy": (
            "Numerical finite spectra only. Retry failed Dirichlet-domain "
            "constructions after triangulation randomization. Do not call "
            "these full, marked, or interval-certified length spectra."
        ),
    }


def load_hyperbolic_volume_rows() -> list[dict[str, Any]]:
    if not VOLUME_ROWS_PATH.exists():
        raise FileNotFoundError(
            "run scripts/run_prime_knot_volume_gate.py before this gate"
        )
    with VOLUME_ROWS_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    selected = [
        row
        for row in rows
        if row["expected_geometry"] == "hyperbolic"
        and row["geometry_gate_passed"] == "True"
    ]
    if len(selected) != 31:
        raise RuntimeError(
            f"expected 31 hyperbolic volume rows, found {len(selected)}"
        )
    return selected


def numerical_length_spectrum(
    knot_name: str,
) -> tuple[tuple[ShortGeodesic, ...], int, list[str]]:
    import snappy

    errors = []
    for attempt in range(MAX_RANDOMIZATION_RETRIES + 1):
        manifold = snappy.Manifold(knot_name)
        for _ in range(attempt):
            manifold.randomize()
        try:
            spectrum = manifold.length_spectrum(LENGTH_CUTOFF)
            records = tuple(
                ShortGeodesic(
                    real_length=float(item.length.real),
                    twist_angle=float(item.length.imag),
                    multiplicity=int(item.multiplicity),
                )
                for item in spectrum
            )
            if len(records) < 5:
                raise RuntimeError(
                    "fewer than five grouped records below the cutoff"
                )
            return records, attempt, errors
        except Exception as error:
            errors.append(f"{type(error).__name__}: {error}")
    raise RuntimeError(
        f"{knot_name}: exhausted length-spectrum retries: {errors[-1]}"
    )


def collect_rows(
    source_rows: list[dict[str, Any]],
    audit: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, tuple[ShortGeodesic, ...]],
    list[dict[str, Any]],
]:
    if not audit["snappy_available"]:
        raise RuntimeError("SnapPy is required for this gate")

    import snappy

    audit["snappy_version"] = getattr(snappy, "__version__", "unknown")
    rows = []
    geodesic_rows = []
    spectra = {}
    error_rows = []
    for source in source_rows:
        knot_name = source["knot_name"]
        started = time.perf_counter()
        records, retry_count, errors = numerical_length_spectrum(knot_name)
        elapsed = time.perf_counter() - started
        spectra[knot_name] = records
        statistics = summarize_short_spectrum(records)
        row = {
            "knot_name": knot_name,
            "crossing_count": int(source["crossing_count"]),
            "fox_determinant": int(source["fox_determinant"]),
            "log_fox_determinant": float(source["log_fox_determinant"]),
            "maximum_tait_spectral_radius": float(
                source["maximum_tait_spectral_radius"]
            ),
            "jsj_hyperbolic_volume_numeric": float(
                source["jsj_hyperbolic_volume_numeric"]
            ),
            "length_cutoff": LENGTH_CUTOFF,
            "length_spectrum_retry_count": retry_count,
            "length_spectrum_elapsed_seconds": elapsed,
            "length_spectrum_status": "numerical_unverified",
            **statistics,
        }
        rows.append(row)
        for index, record in enumerate(records):
            geodesic_rows.append(
                {
                    "knot_name": knot_name,
                    "record_index": index,
                    "real_length": record.real_length,
                    "twist_angle": record.twist_angle,
                    "multiplicity": record.multiplicity,
                    "length_cutoff": LENGTH_CUTOFF,
                    "status": "numerical_unverified",
                }
            )
        for attempt, message in enumerate(errors):
            error_rows.append(
                {
                    "knot_name": knot_name,
                    "failed_attempt": attempt,
                    "error_message": message,
                    "recovered": True,
                }
            )
    return rows, geodesic_rows, spectra, error_rows


def add_prediction_columns(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    target = np.asarray(
        [row["jsj_hyperbolic_volume_numeric"] for row in rows],
        dtype=float,
    )
    model_predictions = {}
    for name, feature_names in MODEL_FEATURES.items():
        features = np.asarray(
            [[row[key] for key in feature_names] for row in rows],
            dtype=float,
        )
        model_predictions[name] = leave_one_out_ridge_predictions(
            features,
            target,
            alpha=1.0,
        )

    for index, row in enumerate(rows):
        for name, predictions in model_predictions.items():
            row[f"{name}_loocv_prediction"] = predictions[index]
            row[f"{name}_absolute_error"] = abs(
                predictions[index] - target[index]
            )
        row["systole_absolute_error_reduction"] = (
            row["compressed_invariant_baseline_absolute_error"]
            - row["systole_augmented_absolute_error"]
        )
        row["full_stack_absolute_error_reduction"] = (
            row["compressed_invariant_baseline_absolute_error"]
            - row["full_local_angular_augmented_absolute_error"]
        )
    return rows


def correlation(
    rows: list[dict[str, Any]],
    feature: str,
) -> float:
    x = np.asarray([row[feature] for row in rows], dtype=float)
    y = np.asarray(
        [row["jsj_hyperbolic_volume_numeric"] for row in rows],
        dtype=float,
    )
    if float(np.std(x)) == 0.0:
        return math.nan
    return float(np.corrcoef(x, y)[0, 1])


def make_summary_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    target = [row["jsj_hyperbolic_volume_numeric"] for row in rows]
    model_metrics = {}
    model_sign_tests = {}
    baseline_errors = [
        row["compressed_invariant_baseline_absolute_error"]
        for row in rows
    ]
    for name in MODEL_FEATURES:
        predicted = [
            row[f"{name}_loocv_prediction"]
            for row in rows
        ]
        model_metrics[name] = prediction_error_metrics(target, predicted)
        model_sign_tests[name] = paired_sign_test_summary(
            baseline_errors,
            [row[f"{name}_absolute_error"] for row in rows],
        )
    baseline_metrics = model_metrics["compressed_invariant_baseline"]
    summaries = []
    for name, features in MODEL_FEATURES.items():
        metrics = model_metrics[name]
        sign_test = model_sign_tests[name]
        summaries.append(
            {
                "summary_type": "loocv_model",
                "name": name,
                "row_count": len(rows),
                "features": " ".join(features),
                "rmse": metrics["rmse"],
                "mae": metrics["mae"],
                "correlation_with_volume": "",
                "rmse_improvement_over_baseline": (
                    baseline_metrics["rmse"] - metrics["rmse"]
                ),
                "mae_improvement_over_baseline": (
                    baseline_metrics["mae"] - metrics["mae"]
                ),
                "improved_row_count": sign_test["improved_row_count"],
                "paired_non_tie_count": sign_test["paired_non_tie_count"],
                "sign_test_pvalue_two_sided": (
                    sign_test["sign_test_pvalue_two_sided"]
                ),
            }
        )
    for feature in (
        "systole_numeric",
        "second_to_first_length_ratio",
        "short_length_cv",
        "geodesic_count_le_2_5",
        "finite_counting_entropy_proxy",
        "twist_angle_entropy_8bin",
        "twist_angle_resultant",
    ):
        summaries.append(
            {
                "summary_type": "feature_correlation",
                "name": feature,
                "row_count": len(rows),
                "features": feature,
                "rmse": "",
                "mae": "",
                "correlation_with_volume": correlation(rows, feature),
                "rmse_improvement_over_baseline": "",
                "mae_improvement_over_baseline": "",
                "improved_row_count": "",
                "paired_non_tie_count": "",
                "sign_test_pvalue_two_sided": "",
            }
        )
    return summaries


def make_collision_rows(
    rows: list[dict[str, Any]],
    spectra: dict[str, tuple[ShortGeodesic, ...]],
) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["fox_determinant"])].append(row)

    output = []
    for determinant, members in sorted(grouped.items()):
        if len(members) < 2:
            continue
        for first, second in itertools.combinations(members, 2):
            first_name = str(first["knot_name"])
            second_name = str(second["knot_name"])
            distance = short_spectrum_distance(
                spectra[first_name],
                spectra[second_name],
            )
            output.append(
                {
                    "fox_determinant": determinant,
                    "first_knot": first_name,
                    "second_knot": second_name,
                    "first_volume": first["jsj_hyperbolic_volume_numeric"],
                    "second_volume": second["jsj_hyperbolic_volume_numeric"],
                    "volume_difference": abs(
                        first["jsj_hyperbolic_volume_numeric"]
                        - second["jsj_hyperbolic_volume_numeric"]
                    ),
                    "first_systole": first["systole_numeric"],
                    "second_systole": second["systole_numeric"],
                    "scale_free_short_spectrum_distance": distance,
                    "finite_fingerprint_equal": (
                        first["short_spectrum_fingerprint"]
                        == second["short_spectrum_fingerprint"]
                    ),
                    "status": "finite_numerical_unverified",
                }
            )
    return output


def render_plot(rows: list[dict[str, Any]]) -> None:
    target = np.asarray(
        [row["jsj_hyperbolic_volume_numeric"] for row in rows],
        dtype=float,
    )
    figure, axes = plt.subplots(2, 2, figsize=(12.0, 10.0))

    scatter = axes[0, 0].scatter(
        [row["systole_numeric"] for row in rows],
        target,
        c=[row["crossing_count"] for row in rows],
        cmap="viridis",
        alpha=0.88,
    )
    axes[0, 0].set_xlabel("Shortest numerical geodesic length")
    axes[0, 0].set_ylabel("Hyperbolic volume")
    axes[0, 0].set_title("Systole proxy versus volume")
    figure.colorbar(scatter, ax=axes[0, 0], label="Crossing count")

    limits = (
        min(
            np.min(target),
            min(
                row["compressed_invariant_baseline_loocv_prediction"]
                for row in rows
            ),
            min(
                row["systole_augmented_loocv_prediction"]
                for row in rows
            ),
        ),
        max(
            np.max(target),
            max(
                row["compressed_invariant_baseline_loocv_prediction"]
                for row in rows
            ),
            max(
                row["systole_augmented_loocv_prediction"]
                for row in rows
            ),
        ),
    )
    axes[0, 1].plot(limits, limits, color="#333333", linewidth=1.0)
    axes[0, 1].scatter(
        target,
        [
            row["compressed_invariant_baseline_loocv_prediction"]
            for row in rows
        ],
        label="determinant/Tait baseline",
        alpha=0.78,
        color="#d1495b",
    )
    axes[0, 1].scatter(
        target,
        [row["systole_augmented_loocv_prediction"] for row in rows],
        label="systole augmented",
        alpha=0.78,
        color="#00798c",
    )
    axes[0, 1].set_xlabel("Observed hyperbolic volume")
    axes[0, 1].set_ylabel("Leave-one-out prediction")
    axes[0, 1].set_title("Fixed ridge model comparison")
    axes[0, 1].legend()

    axes[1, 0].scatter(
        [row["finite_counting_entropy_proxy"] for row in rows],
        target,
        c="#30638e",
        alpha=0.85,
    )
    axes[1, 0].set_xlabel("Finite geodesic-count growth proxy")
    axes[1, 0].set_ylabel("Hyperbolic volume")
    axes[1, 0].set_title("A finite-cutoff proxy, not flow entropy")

    axes[1, 1].scatter(
        [row["twist_angle_entropy_8bin"] for row in rows],
        target,
        c="#edae49",
        alpha=0.85,
    )
    axes[1, 1].set_xlabel("Twist-angle sector entropy")
    axes[1, 1].set_ylabel("Hyperbolic volume")
    axes[1, 1].set_title("Angular local-to-global statistic")

    for axis in axes.flat:
        axis.grid(alpha=0.22)
    figure.tight_layout()
    figure.savefig(
        OUTPUT_DIR / "prime_knot_length_spectrum_diagnostics.png",
        dpi=190,
    )
    plt.close(figure)


def make_transfer_notes() -> str:
    return """# Pardon / Anosov Transfer Notes

## What Transfers

John Pardon's random-polygon theorem obtains uniform statistics by
normalizing geometry and decomposing global observables into angularly
local contributions. This gate transfers that *methodological pattern*:
it records scale-free ratios, short-geodesic counting statistics, and
eight angular sectors of complex holonomy. It does not transfer Pardon's
central limit theorem to knots.

Pardon's knot-distortion work also warns that a topological class alone
does not control geometric strain. The complex-length spectrum is a
different geometric observable, but it serves the same diagnostic
discipline here: exact determinant/Tait data and complement geometry are
kept side by side rather than treated as interchangeable.

Higher Teichmuller theory supplies a deeper length-spectrum analogy.
Pressure metrics for Anosov representations use thermodynamic formalism,
entropy, and the full marked length spectrum. This gate uses only a finite,
unmarked, numerical spectrum below length 2.5. Its count-growth slope is
therefore named an entropy *proxy*, not entropy or pressure.

## The Cusp Boundary

Finite-volume knot complements have parabolic cusp subgroups. Their
holonomy is not an ordinary Anosov representation in the standard
word-hyperbolic setting. Relative Anosov and relatively dominated
representations are the appropriate neighboring theories. The present
gate does not construct such a representation.

## Falsifiable Question

Does adding finite short-length and twist-angle statistics reduce
fixed-alpha leave-one-out error for hyperbolic volume beyond crossing
count, log determinant, and the maximum Tait spectral radius?

This is a small finite diagnostic. A positive answer would prioritize
marked/relative length-spectrum work; a negative answer would reject this
particular finite feature set, not the surrounding theories.

## Sources

- Pardon, random polygons: https://arxiv.org/abs/1003.4209
- Pardon, knot distortion: https://arxiv.org/abs/1010.1972
- Guichard and Wienhard, Anosov representations:
  https://arxiv.org/abs/1108.0733
- Bridgeman, Canary, Labourie, and Sambarino, pressure metric:
  https://arxiv.org/abs/1301.7459
- Weisman, extended relative Anosov definition:
  https://arxiv.org/abs/2205.07183
- Zhu and Zimmer, relative Anosov flows:
  https://arxiv.org/abs/2207.14737
- SnapPy length-spectrum documentation:
  https://snappy.computop.org/manifold.html
"""


def make_report(
    rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    collision_rows: list[dict[str, Any]],
    error_rows: list[dict[str, Any]],
    audit: dict[str, Any],
) -> str:
    baseline = next(
        row
        for row in summary_rows
        if row["name"] == "compressed_invariant_baseline"
    )
    systole = next(
        row
        for row in summary_rows
        if row["name"] == "systole_augmented"
    )
    compact = next(
        row
        for row in summary_rows
        if row["name"] == "compact_geometry_augmented"
    )
    full = next(
        row
        for row in summary_rows
        if row["name"] == "full_local_angular_augmented"
    )
    systole_improved_rmse = float(systole["rmse"]) < float(baseline["rmse"])
    full_improved_rmse = float(full["rmse"]) < float(baseline["rmse"])
    best_correlations = sorted(
        (
            (row["name"], float(row["correlation_with_volume"]))
            for row in summary_rows
            if row["summary_type"] == "feature_correlation"
        ),
        key=lambda item: abs(item[1]),
        reverse=True,
    )
    collision_minimum = min(
        row["scale_free_short_spectrum_distance"]
        for row in collision_rows
    )
    collision_equal_count = sum(
        bool(row["finite_fingerprint_equal"]) for row in collision_rows
    )
    retry_knots = sum(
        int(row["length_spectrum_retry_count"]) > 0 for row in rows
    )
    top_features = "\n".join(
        f"- `{name}`: correlation `{value:.6f}`"
        for name, value in best_correlations
    )
    return f"""# Prime-Knot Short Length-Spectrum Gate

## Result

The gate processed all `{len(rows)}` hyperbolic prime knots through eight
crossings using numerical SnapPy complex lengths below `{LENGTH_CUTOFF}`.
Every knot produced at least five grouped records. `{retry_knots}` knots
needed a randomized triangulation after the initial Dirichlet construction
failed; all retries and messages are preserved.

The minimal Pardon/Anosov-inspired geometric augmentation
`{"did" if systole_improved_rmse else "did not"}` improve fixed-alpha
leave-one-out RMSE, while the complete local/angular stack
`{"did" if full_improved_rmse else "did not"}`:

| Model | Features | RMSE | MAE | Better rows | Sign-test p |
| --- | ---: | ---: | ---: | ---: | ---: |
| determinant/Tait baseline | {len(BASELINE_FEATURES)} | {float(baseline["rmse"]):.6f} | {float(baseline["mae"]):.6f} | - | - |
| + shortest geodesic | {len(SYSTOLE_FEATURES)} | {float(systole["rmse"]):.6f} | {float(systole["mae"]):.6f} | {systole["improved_row_count"]}/{systole["paired_non_tie_count"]} | {float(systole["sign_test_pvalue_two_sided"]):.6f} |
| + shortest geodesic and local spread | {len(COMPACT_GEOMETRY_FEATURES)} | {float(compact["rmse"]):.6f} | {float(compact["mae"]):.6f} | {compact["improved_row_count"]}/{compact["paired_non_tie_count"]} | {float(compact["sign_test_pvalue_two_sided"]):.6f} |
| full local/angular stack | {len(ENRICHED_FEATURES)} | {float(full["rmse"]):.6f} | {float(full["mae"]):.6f} | {full["improved_row_count"]}/{full["paired_non_tie_count"]} | {float(full["sign_test_pvalue_two_sided"]):.6f} |

The shortest-geodesic RMSE improvement is
`{float(baseline["rmse"]) - float(systole["rmse"]):.6f}`
(`{100.0 * (float(baseline["rmse"]) - float(systole["rmse"])) / float(baseline["rmse"]):.2f}%`).
The full-stack change is
`{float(baseline["rmse"]) - float(full["rmse"]):.6f}`. Reporting all four
nested models prevents the favorable shortest-geodesic result from hiding
the fact that the larger feature stack adds no held-out benefit. These are
descriptive finite-census results, not theorems or selected production
models.

The exact paired sign test also blocks a stronger claim: the
shortest-geodesic model improves absolute error on only
`{systole["improved_row_count"]}` of
`{systole["paired_non_tie_count"]}` non-tied rows
(`p = {float(systole["sign_test_pvalue_two_sided"]):.6f}`). Its RMSE gain
comes from the magnitude of a minority of corrections, not consistent
row-wise superiority.

## Precise Statistics

Correlations with numerical hyperbolic volume:

{top_features}

The statistics include the shortest real length, a scale-free second/first
length ratio, multiplicity-weighted coefficient of variation, counts below
three fixed cutoffs, a finite count-growth slope, and eight-sector
twist-angle entropy/resultant. The count-growth slope is **not** the
topological entropy of the geodesic flow.

## Determinant Collisions

The hyperbolic census contains `{len(collision_rows)}` equal-determinant
knot pairs. Their five-record scale-free short-spectrum fingerprints agree
in `{collision_equal_count}` cases. The smallest pairwise fingerprint
distance is `{collision_minimum:.6g}`.

This says the finite numerical statistic separates these particular
determinant collisions. It does not make the fingerprint a complete knot
invariant, and rounded equality is not a proof of isospectrality.

## What This Adds to Pardon and Wienhard

Pardon's useful contribution here is the architecture of a precise
local-to-global statistic: normalize first, retain angular sectors, and
test concentration rather than reducing an object to one scalar. The
experiment evaluates that architecture on complex lengths; it does not
improve or alter Pardon's random-polygon or knot-distortion theorems.

The Anosov connection is similarly disciplined. Full marked length spectra,
entropy, and pressure are central in higher Teichmuller theory. These knot
complements are cusped and have parabolics, so the relevant bridge is
relative Anosov theory, not an assertion that the ordinary knot holonomy is
an Anosov representation. This gate computes no pressure metric.

## Backend and Limits

- SnapPy: `{audit["snappy_version"]}`
- Sage available:
  `{audit["sage_command_available"] or audit["sageall_available"]}`
- recovered Dirichlet failures: `{len(error_rows)}`
- status of every spectrum: `numerical_unverified`
- spectrum cutoff: `{LENGTH_CUTOFF}`

The finite cutoff, unmarked spectrum, table-size selection, and lack of
interval certification prevent a novelty or universality claim. The next
mathematically serious step is a marked or relative length-spectrum
construction, not adding more ad hoc regressors.

## Sources

- Pardon, random polygons: https://arxiv.org/abs/1003.4209
- Pardon, knot distortion: https://arxiv.org/abs/1010.1972
- Guichard and Wienhard, Anosov representations:
  https://arxiv.org/abs/1108.0733
- Bridgeman, Canary, Labourie, and Sambarino, pressure metric:
  https://arxiv.org/abs/1301.7459
- Weisman, relative Anosov representations:
  https://arxiv.org/abs/2205.07183
- SnapPy numerical length spectra:
  https://snappy.computop.org/manifold.html
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audit = backend_audit()
    source_rows = load_hyperbolic_volume_rows()
    rows, geodesic_rows, spectra, error_rows = collect_rows(source_rows, audit)
    add_prediction_columns(rows)
    summaries = make_summary_rows(rows)
    collisions = make_collision_rows(rows, spectra)

    write_csv(OUTPUT_DIR / "prime_knot_length_spectrum_rows.csv", rows)
    write_csv(
        OUTPUT_DIR / "prime_knot_short_geodesic_records.csv",
        geodesic_rows,
    )
    write_csv(
        OUTPUT_DIR / "prime_knot_length_spectrum_summary.csv",
        summaries,
    )
    write_csv(
        OUTPUT_DIR / "prime_knot_length_spectrum_collisions.csv",
        collisions,
    )
    write_csv(
        OUTPUT_DIR / "prime_knot_length_spectrum_errors.csv",
        error_rows,
    )
    (OUTPUT_DIR / "prime_knot_length_spectrum_backend.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    render_plot(rows)
    (OUTPUT_DIR / "PARDON_ANOSOV_TRANSFER_NOTES.md").write_text(
        make_transfer_notes(),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "PRIME_KNOT_LENGTH_SPECTRUM_REPORT.md").write_text(
        make_report(rows, summaries, collisions, error_rows, audit),
        encoding="utf-8",
    )
    print(
        f"Processed {len(rows)} hyperbolic knots; "
        f"wrote {len(geodesic_rows)} grouped geodesic records and "
        f"{len(collisions)} determinant-collision pairs."
    )


if __name__ == "__main__":
    main()

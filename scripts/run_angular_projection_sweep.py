"""Sweep polygonal-knot projections over deterministic sphere directions."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import statistics
import sys
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from four_color_diagnostics.geometry import fibonacci_sphere_directions
from run_polygonal_projection_stability import (
    FIXTURES,
    extract_row,
    load_backends,
    write_csv,
)


OUTPUT_DIR = ROOT / "results"
DIRECTION_COUNT = 128
POLYGON_SAMPLES = 96


def build_rows(knot_class: Any, link_class: Any | None) -> list[dict[str, Any]]:
    rows = []
    directions = fibonacci_sphere_directions(DIRECTION_COUNT)
    for fixture in FIXTURES:
        points = fixture.generator(POLYGON_SAMPLES)
        for direction_index, direction_array in enumerate(directions):
            direction = tuple(float(value) for value in direction_array)
            row = extract_row(
                knot_class,
                link_class,
                fixture,
                "deterministic_angular_sweep",
                POLYGON_SAMPLES,
                None,
                f"fibonacci_{direction_index:03d}",
                direction,
                points,
            )
            row.update(
                {
                    "direction_index": direction_index,
                    "direction_x": direction[0],
                    "direction_y": direction[1],
                    "direction_z": direction[2],
                    "longitude_radians": float(
                        np.arctan2(direction[1], direction[0])
                    ),
                    "latitude_radians": float(np.arcsin(direction[2])),
                    "raw_minimal_diagram_pass": bool(
                        row["extraction_status"] == "passed"
                        and row["crossing_count"]
                        == row["expected_crossing_count"]
                        and row["determinant_matches_expected"]
                    ),
                    "extra_raw_crossings": (
                        int(row["crossing_count"])
                        - int(row["expected_crossing_count"])
                        if row["extraction_status"] == "passed"
                        else ""
                    ),
                }
            )
            rows.append(row)
    return rows


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for fixture in FIXTURES:
        selected = [row for row in rows if row["fixture"] == fixture.name]
        passed = [
            row for row in selected if row["extraction_status"] == "passed"
        ]
        output.append(
            {
                "fixture": fixture.name,
                "direction_count": len(selected),
                "extraction_pass_count": len(passed),
                "determinant_pass_count": sum(
                    bool(row["determinant_matches_expected"])
                    for row in selected
                ),
                "raw_minimal_diagram_count": sum(
                    bool(row["raw_minimal_diagram_pass"]) for row in selected
                ),
                "simplified_fixture_pass_count": sum(
                    bool(row["topological_fixture_pass"]) for row in selected
                ),
                "alternating_projection_count": sum(
                    bool(row["alternating_projection"]) for row in passed
                ),
                "minimum_raw_crossings": (
                    min(int(row["crossing_count"]) for row in passed)
                    if passed
                    else ""
                ),
                "maximum_raw_crossings": (
                    max(int(row["crossing_count"]) for row in passed)
                    if passed
                    else ""
                ),
                "minimum_crossing_angle_degrees": (
                    min(
                        float(row["minimum_crossing_angle_degrees"])
                        for row in passed
                    )
                    if passed
                    else ""
                ),
                "minimum_crossing_vertex_parameter_margin": (
                    min(
                        float(
                            row["minimum_crossing_vertex_parameter_margin"]
                        )
                        for row in passed
                    )
                    if passed
                    else ""
                ),
                "total_runtime_seconds": sum(
                    float(row["runtime_seconds"]) for row in selected
                ),
            }
        )
    return output


def margin_bucket_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for fixture in FIXTURES:
        selected = [row for row in rows if row["fixture"] == fixture.name]
        buckets = {
            "raw_minimal": [
                row for row in selected if row["raw_minimal_diagram_pass"]
            ],
            "extra_simplified_to_fixture": [
                row
                for row in selected
                if not row["raw_minimal_diagram_pass"]
                and row["topological_fixture_pass"]
            ],
            "extra_unresolved_by_basic_simplifier": [
                row
                for row in selected
                if not row["raw_minimal_diagram_pass"]
                and not row["topological_fixture_pass"]
            ],
        }
        for bucket, bucket_rows in buckets.items():
            if not bucket_rows:
                continue
            output.append(
                {
                    "fixture": fixture.name,
                    "bucket": bucket,
                    "row_count": len(bucket_rows),
                    "mean_raw_crossing_count": statistics.mean(
                        float(row["crossing_count"]) for row in bucket_rows
                    ),
                    "mean_minimum_crossing_angle_degrees": statistics.mean(
                        float(row["minimum_crossing_angle_degrees"])
                        for row in bucket_rows
                    ),
                    "median_crossing_vertex_parameter_margin": (
                        statistics.median(
                            float(
                                row[
                                    "minimum_crossing_vertex_parameter_margin"
                                ]
                            )
                            for row in bucket_rows
                        )
                    ),
                    "mean_normalized_minimum_depth_separation": (
                        statistics.mean(
                            float(
                                row[
                                    "normalized_minimum_depth_separation"
                                ]
                            )
                            for row in bucket_rows
                        )
                    ),
                }
            )
    return output


def render_direction_plot(rows: list[dict[str, Any]]) -> None:
    maximum_extra = max(
        (
            int(row["extra_raw_crossings"])
            for row in rows
            if row["extraction_status"] == "passed"
        ),
        default=1,
    )
    figure, axes = plt.subplots(
        1,
        3,
        figsize=(14.0, 4.8),
        subplot_kw={"projection": "mollweide"},
    )
    scatter = None
    for axis, fixture in zip(axes, FIXTURES, strict=True):
        selected = [row for row in rows if row["fixture"] == fixture.name]
        passed = [
            row for row in selected if row["extraction_status"] == "passed"
        ]
        scatter = axis.scatter(
            [float(row["longitude_radians"]) for row in passed],
            [float(row["latitude_radians"]) for row in passed],
            c=[int(row["extra_raw_crossings"]) for row in passed],
            cmap="viridis",
            vmin=0,
            vmax=maximum_extra,
            s=25,
            linewidths=[
                0.9 if not bool(row["determinant_matches_expected"]) else 0.0
                for row in passed
            ],
            edgecolors=[
                "#d62728"
                if not bool(row["determinant_matches_expected"])
                else "none"
                for row in passed
            ],
        )
        failed = [
            row for row in selected if row["extraction_status"] == "failed"
        ]
        if failed:
            axis.scatter(
                [float(row["longitude_radians"]) for row in failed],
                [float(row["latitude_radians"]) for row in failed],
                color="#d62728",
                marker="x",
                s=38,
                linewidths=1.3,
            )
        axis.set_title(fixture.name)
        axis.grid(alpha=0.28)
    if scatter is not None:
        colorbar = figure.colorbar(
            scatter,
            ax=axes,
            orientation="horizontal",
            fraction=0.08,
            pad=0.14,
        )
        colorbar.set_label("extra raw crossings above fixture minimum")
    figure.suptitle(
        "Deterministic angular projection sweep (Fibonacci sphere)",
        fontsize=14,
    )
    figure.subplots_adjust(left=0.04, right=0.98, top=0.84, bottom=0.2, wspace=0.08)
    figure.savefig(OUTPUT_DIR / "angular_projection_sweep.png", dpi=190)
    plt.close(figure)


def make_report(
    rows: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    margin_buckets: list[dict[str, Any]],
    backend: dict[str, Any],
) -> str:
    table = "\n".join(
        "| {fixture} | {extraction_pass_count}/{direction_count} | "
        "{determinant_pass_count}/{direction_count} | "
        "{raw_minimal_diagram_count}/{direction_count} | "
        "{simplified_fixture_pass_count}/{direction_count} | "
        "{alternating_projection_count} | {minimum_raw_crossings} | "
        "{maximum_raw_crossings} | {minimum_crossing_angle_degrees:.4f} | "
        "{minimum_crossing_vertex_parameter_margin:.6g} |".format(**row)
        for row in summaries
    )
    failures = [row for row in rows if row["extraction_status"] == "failed"]
    determinant_failures = [
        row
        for row in rows
        if row["extraction_status"] == "passed"
        and not bool(row["determinant_matches_expected"])
    ]
    simplified_failures = [
        row for row in rows if not bool(row["topological_fixture_pass"])
    ]
    margin_table = "\n".join(
        "| {fixture} | {bucket} | {row_count} | "
        "{mean_raw_crossing_count:.3f} | "
        "{mean_minimum_crossing_angle_degrees:.3f} | "
        "{median_crossing_vertex_parameter_margin:.5f} | "
        "{mean_normalized_minimum_depth_separation:.5f} |".format(**row)
        for row in margin_buckets
    )
    return f"""# Angular Projection Sweep Report

## Result

The sweep tested `{DIRECTION_COUNT}` deterministic Fibonacci-sphere
directions on each of three `{POLYGON_SAMPLES}`-vertex polygonal knots,
for `{len(rows)}` total rows.

- Extraction failures: `{len(failures)}`.
- Fox-determinant mismatches: `{len(determinant_failures)}`.
- Rows not reduced to the minimal fixture by the bounded simplifier:
  `{len(simplified_failures)}`.

| Fixture | Extracted | Determinant | Raw minimal | Simplified fixture | Alternating | Min crossings | Max crossings | Min angle | Min vertex margin |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{table}

Raw crossing count is projection-dependent. A direction that produces more
than the tabulated minimal crossing number is not a topological failure.
The Fox determinant is retained as a cheap invariant check, while the
Spherogram `basic` simplifier supplies a stronger but incomplete fixture
reduction check. Failure of that bounded simplifier is not evidence that
the knot type changed.

## Angular Interpretation

The direction set is deterministic and approximately area-uniform on the
sphere. It is a finite angular audit inspired by Pardon's local-to-global
decomposition of random polygon statistics, not an application of his
central limit theorem. The recorded crossing-angle, crossing-depth, and
crossing-to-vertex margins expose directions near projection walls where
diagram extraction is least robust.

| Fixture | Direction bucket | Count | Mean crossings | Mean min angle | Median vertex margin | Mean min depth |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
{margin_table}

Across these fixtures, raw-minimal directions have larger mean crossing
angles and larger median crossing-to-vertex margins than directions with
extra crossings. This is a descriptive finite-sample pattern, not a proof
that either margin controls diagram complexity.

## Backend

- Python: `{backend["python_executable"]}`
- pyknotid: `{backend.get("pyknotid_version", "unavailable")}`
- Spherogram: `{backend.get("spherogram_version", "unavailable")}`
- planarity extension available: `{backend["planarity_available"]}`

## Scope

This finite sweep does not estimate the exact spherical measure of bad
directions, certify generic projection, classify the knots, or prove a new
result in knot theory. It provides reproducible evidence and a set of
adversarial projection directions for a later interval-certified gate.

## Sources

- John Pardon, *Central limit theorems for random polygons in an arbitrary
  convex set*: https://arxiv.org/abs/1003.4209
- pyknotid space-curve documentation:
  https://pyknotid.readthedocs.io/en/latest/sources/spacecurves/spacecurve.html
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    knot_class, link_class, backend = load_backends()
    if knot_class is None:
        raise SystemExit(
            "pyknotid is unavailable; run the projection stability backend audit"
        )
    rows = build_rows(knot_class, link_class)
    summaries = summarize(rows)
    margin_buckets = margin_bucket_summary(rows)
    write_csv(OUTPUT_DIR / "angular_projection_sweep_rows.csv", rows)
    write_csv(OUTPUT_DIR / "angular_projection_sweep_summary.csv", summaries)
    write_csv(
        OUTPUT_DIR / "angular_projection_margin_buckets.csv",
        margin_buckets,
    )
    error_rows = [
        {
            "fixture": row["fixture"],
            "direction_index": row["direction_index"],
            "projection_direction": row["projection_direction"],
            "extraction_status": row["extraction_status"],
            "determinant_matches_expected": row["determinant_matches_expected"],
            "simplification_status": row["simplification_status"],
            "error_message": (
                row["error_message"] or row["simplification_error"]
            ),
        }
        for row in rows
        if row["extraction_status"] == "failed"
        or not bool(row["determinant_matches_expected"])
        or row["simplification_status"] == "failed"
    ]
    write_csv(
        OUTPUT_DIR / "angular_projection_sweep_errors.csv",
        error_rows,
        fieldnames=[
            "fixture",
            "direction_index",
            "projection_direction",
            "extraction_status",
            "determinant_matches_expected",
            "simplification_status",
            "error_message",
        ],
    )
    render_direction_plot(rows)
    (OUTPUT_DIR / "ANGULAR_PROJECTION_SWEEP_REPORT.md").write_text(
        make_report(rows, summaries, margin_buckets, backend),
        encoding="utf-8",
    )
    print(
        f"Angular projection sweep: {len(rows)} rows; "
        f"{sum(row['extraction_status'] == 'failed' for row in rows)} "
        "extraction failures"
    )


if __name__ == "__main__":
    main()

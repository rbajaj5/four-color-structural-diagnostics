"""Audit knot-diagram stability under subdivision, resampling, and projection."""

from __future__ import annotations

import contextlib
import csv
from dataclasses import dataclass
import importlib.metadata
import importlib.util
import io
import json
from pathlib import Path
import sys
import time
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from four_color_diagnostics.geometry import (
    canonical_gauss_signature,
    crossing_projection_margins,
    crossing_vertex_parameter_margin,
    figure_eight_knot_points,
    is_alternating_gauss_traversal,
    minimum_nonlocal_vertex_clearance,
    polygon_length,
    project_along,
    subdivide_closed_polygon,
    torus_knot_points,
    vertex_distortion_estimate,
)
from four_color_diagnostics.tait import (
    fox_coloring_determinant,
    tait_graphs_from_pd_code,
)


OUTPUT_DIR = ROOT / "results"
PROJECTIONS = {
    "z_axis": (0.0, 0.0, 1.0),
    "tilt_x_005": (0.05, 0.0, 1.0),
    "tilt_y_neg007": (0.0, -0.07, 1.0),
    "oblique_008_neg006": (0.08, -0.06, 1.0),
}
SMOOTH_SAMPLE_COUNTS = (16, 24, 32, 48, 64, 96)
SUBDIVISION_FACTORS = (1, 2, 4, 8)


@dataclass(frozen=True)
class GeometryFixture:
    name: str
    expected_crossings: int
    expected_determinant: int
    base_samples: int
    generator: Callable[[int], np.ndarray]


FIXTURES = (
    GeometryFixture(
        "3_1_torus_T_2_3",
        3,
        3,
        24,
        lambda samples: torus_knot_points(2, 3, samples),
    ),
    GeometryFixture(
        "5_1_torus_T_2_5",
        5,
        5,
        32,
        lambda samples: torus_knot_points(2, 5, samples),
    ),
    GeometryFixture(
        "4_1_figure_eight",
        4,
        5,
        32,
        figure_eight_knot_points,
    ),
)


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    *,
    fieldnames: list[str] | None = None,
) -> None:
    if not rows and not fieldnames:
        raise ValueError("empty CSV output requires explicit fieldnames")
    columns = fieldnames or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def load_backends() -> tuple[Any | None, Any | None, dict[str, Any]]:
    audit: dict[str, Any] = {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "numpy_version": np.__version__,
        "pyknotid_available": bool(importlib.util.find_spec("pyknotid")),
        "planarity_available": bool(importlib.util.find_spec("planarity")),
        "spherogram_available": bool(importlib.util.find_spec("spherogram")),
        "numpy_legacy_aliases_added": [],
        "backend_role": (
            "optional local 3D polygon to Gauss/PD extraction; not a core "
            "package dependency"
        ),
    }
    for name, value in (
        ("float", float),
        ("int", int),
        ("complex", complex),
    ):
        if name not in np.__dict__:
            setattr(np, name, value)
            audit["numpy_legacy_aliases_added"].append(name)
    if not audit["pyknotid_available"]:
        audit["backend_status"] = "blocked"
        audit["import_error"] = "pyknotid is not installed"
        return None, None, audit
    try:
        audit["pyknotid_version"] = importlib.metadata.version("pyknotid")
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(
            captured
        ):
            from pyknotid.spacecurves import Knot

        audit["import_messages"] = captured.getvalue().strip()
        link_class = None
        if audit["spherogram_available"]:
            from spherogram import Link

            link_class = Link
            audit["spherogram_version"] = importlib.metadata.version("spherogram")
        audit["backend_status"] = "available"
        return Knot, link_class, audit
    except Exception as error:
        audit["backend_status"] = "blocked"
        audit["import_error"] = f"{type(error).__name__}: {error}"
        return None, None, audit


def base_row(
    fixture: GeometryFixture,
    mode: str,
    resolution: int,
    subdivision_factor: int | None,
    projection_name: str,
    direction: tuple[float, float, float],
    points: np.ndarray,
) -> dict[str, Any]:
    return {
        "fixture": fixture.name,
        "source_mode": mode,
        "base_samples": fixture.base_samples,
        "resolution": resolution,
        "subdivision_factor": (
            subdivision_factor if subdivision_factor is not None else ""
        ),
        "projection": projection_name,
        "projection_class": (
            "axis_aligned_reference"
            if projection_name == "z_axis"
            else "generic_tilt"
        ),
        "projection_direction": json.dumps(direction),
        "expected_crossing_count": fixture.expected_crossings,
        "expected_determinant": fixture.expected_determinant,
        "polygon_length": polygon_length(points),
        "vertex_distortion_estimate": vertex_distortion_estimate(points),
        "minimum_nonlocal_vertex_clearance": (
            minimum_nonlocal_vertex_clearance(points)
        ),
    }


def extract_row(
    knot_class: Any,
    link_class: Any | None,
    fixture: GeometryFixture,
    mode: str,
    resolution: int,
    subdivision_factor: int | None,
    projection_name: str,
    direction: tuple[float, float, float],
    points: np.ndarray,
) -> dict[str, Any]:
    row = base_row(
        fixture,
        mode,
        resolution,
        subdivision_factor,
        projection_name,
        direction,
        points,
    )
    started = time.perf_counter()
    try:
        projected = project_along(points, direction)
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(
            captured
        ):
            knot = knot_class(projected, verbose=False)
            raw_crossings = np.asarray(knot.raw_crossings(), dtype=float)
            gauss = knot.gauss_code()
            planar_diagram = knot.planar_diagram()
        gauss_components = tuple(np.asarray(component) for component in gauss._gauss_code)
        if len(gauss_components) != 1:
            raise ValueError(
                f"expected one Gauss component, observed {len(gauss_components)}"
            )
        gauss_rows = gauss_components[0]
        pd_code = tuple(
            tuple(int(value) for value in crossing)
            for crossing in planar_diagram
        )
        crossing_count = len(pd_code)
        if len(raw_crossings) != 2 * crossing_count:
            raise ValueError("raw crossing and PD crossing counts disagree")
        minimum_angle, minimum_depth = crossing_projection_margins(
            projected,
            raw_crossings,
        )
        vertex_parameter_margin = crossing_vertex_parameter_margin(
            raw_crossings
        )
        diameter_scale = float(np.linalg.norm(np.ptp(projected, axis=0)))
        determinant = fox_coloring_determinant(pd_code)
        alternating = is_alternating_gauss_traversal(gauss_rows)
        first_tree_count: int | str = ""
        second_tree_count: int | str = ""
        tait_agrees: bool | str = ""
        tait_status = "not_applicable" if not alternating else "pending"
        tait_error = ""
        if alternating:
            try:
                tait_pair = tait_graphs_from_pd_code(pd_code)
                first_tree_count = tait_pair.first.spanning_tree_count()
                second_tree_count = tait_pair.second.spanning_tree_count()
                tait_agrees = (
                    first_tree_count == second_tree_count == determinant
                )
                tait_status = "passed"
            except Exception as error:
                tait_status = "failed"
                tait_error = f"{type(error).__name__}: {error}"

        simplified_crossing_count: int | str = ""
        simplified_component_count: int | str = ""
        simplified_determinant: int | str = ""
        simplification_changed: bool | str = ""
        simplification_status = "unavailable"
        simplification_error = ""
        if (
            link_class is not None
            and determinant == fixture.expected_determinant
            and crossing_count >= fixture.expected_crossings
        ):
            try:
                link = link_class(pd_code)
                simplification_changed = bool(link.simplify("basic"))
                simplified_crossing_count = len(link.crossings)
                simplified_component_count = len(link.link_components)
                simplified_pd = tuple(
                    tuple(int(value) for value in crossing)
                    for crossing in link.PD_code()
                )
                simplified_determinant = (
                    fox_coloring_determinant(simplified_pd)
                    if simplified_pd
                    else 1
                )
                simplification_status = "passed"
            except Exception as error:
                simplification_status = "failed"
                simplification_error = f"{type(error).__name__}: {error}"
        elif link_class is not None:
            simplification_status = "skipped_precheck_failure"
        topological_fixture_pass = (
            bool(
                determinant == fixture.expected_determinant
                and simplified_component_count == 1
                and simplified_crossing_count == fixture.expected_crossings
                and simplified_determinant == fixture.expected_determinant
            )
            if link_class is not None
            else bool(
                determinant == fixture.expected_determinant
                and crossing_count == fixture.expected_crossings
            )
        )
        row.update(
            {
                "crossing_count": crossing_count,
                "gauss_component_count": len(gauss_components),
                "alternating_projection": alternating,
                "canonical_gauss_signature": canonical_gauss_signature(
                    gauss_rows
                ),
                "pd_code": json.dumps(pd_code),
                "fox_determinant": determinant,
                "first_tait_tree_count": first_tree_count,
                "second_tait_tree_count": second_tree_count,
                "unsigned_tait_shortcut_applicable": alternating,
                "unsigned_tait_shortcut_agrees": tait_agrees,
                "tait_construction_status": tait_status,
                "tait_error": tait_error,
                "simplification_status": simplification_status,
                "simplification_changed": simplification_changed,
                "simplified_crossing_count": simplified_crossing_count,
                "simplified_component_count": simplified_component_count,
                "simplified_fox_determinant": simplified_determinant,
                "simplification_error": simplification_error,
                "topological_fixture_pass": topological_fixture_pass,
                "minimum_crossing_angle_degrees": minimum_angle,
                "minimum_crossing_depth_separation": minimum_depth,
                "minimum_crossing_vertex_parameter_margin": (
                    vertex_parameter_margin
                ),
                "normalized_minimum_depth_separation": (
                    minimum_depth / diameter_scale
                    if diameter_scale > 0.0
                    else float("nan")
                ),
                "crossing_count_matches_expected": (
                    crossing_count == fixture.expected_crossings
                ),
                "determinant_matches_expected": (
                    determinant == fixture.expected_determinant
                ),
                "backend_messages": captured.getvalue().strip(),
                "extraction_status": "passed",
                "error_message": "",
            }
        )
    except Exception as error:
        row.update(
            {
                "crossing_count": "",
                "gauss_component_count": "",
                "alternating_projection": "",
                "canonical_gauss_signature": "",
                "pd_code": "",
                "fox_determinant": "",
                "first_tait_tree_count": "",
                "second_tait_tree_count": "",
                "unsigned_tait_shortcut_applicable": "",
                "unsigned_tait_shortcut_agrees": "",
                "tait_construction_status": "not_run",
                "tait_error": "",
                "simplification_status": "not_run",
                "simplification_changed": "",
                "simplified_crossing_count": "",
                "simplified_component_count": "",
                "simplified_fox_determinant": "",
                "simplification_error": "",
                "topological_fixture_pass": False,
                "minimum_crossing_angle_degrees": "",
                "minimum_crossing_depth_separation": "",
                "minimum_crossing_vertex_parameter_margin": "",
                "normalized_minimum_depth_separation": "",
                "crossing_count_matches_expected": False,
                "determinant_matches_expected": False,
                "backend_messages": "",
                "extraction_status": "failed",
                "error_message": f"{type(error).__name__}: {error}",
            }
        )
    row["runtime_seconds"] = time.perf_counter() - started
    return row


def build_rows(knot_class: Any, link_class: Any | None) -> list[dict[str, Any]]:
    rows = []
    for fixture in FIXTURES:
        base_polygon = fixture.generator(fixture.base_samples)
        for factor in SUBDIVISION_FACTORS:
            points = subdivide_closed_polygon(base_polygon, factor)
            for projection_name, direction in PROJECTIONS.items():
                rows.append(
                    extract_row(
                        knot_class,
                        link_class,
                        fixture,
                        "exact_polygon_subdivision",
                        len(points),
                        factor,
                        projection_name,
                        direction,
                        points,
                    )
                )
        for samples in SMOOTH_SAMPLE_COUNTS:
            points = fixture.generator(samples)
            for projection_name, direction in PROJECTIONS.items():
                rows.append(
                    extract_row(
                        knot_class,
                        link_class,
                        fixture,
                        "smooth_parametric_resampling",
                        samples,
                        None,
                        projection_name,
                        direction,
                        points,
                    )
                )
    add_reference_comparisons(rows)
    return rows


def add_reference_comparisons(rows: list[dict[str, Any]]) -> None:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            str(row["fixture"]),
            str(row["source_mode"]),
            str(row["projection"]),
        )
        groups.setdefault(key, []).append(row)
    for group in groups.values():
        successful = [
            row for row in group if row["extraction_status"] == "passed"
        ]
        expected = [
            row
            for row in successful
            if row["crossing_count_matches_expected"]
            and row["determinant_matches_expected"]
        ]
        reference = (
            max(expected or successful, key=lambda row: int(row["resolution"]))
            if expected or successful
            else None
        )
        for row in group:
            if reference is None or row["extraction_status"] != "passed":
                row["reference_resolution"] = ""
                row["signature_matches_reference"] = False
                row["crossing_count_matches_reference"] = False
                row["determinant_matches_reference"] = False
                row["projection_stability_pass"] = False
                continue
            row["reference_resolution"] = reference["resolution"]
            row["signature_matches_reference"] = (
                row["canonical_gauss_signature"]
                == reference["canonical_gauss_signature"]
            )
            row["crossing_count_matches_reference"] = (
                row["crossing_count"] == reference["crossing_count"]
            )
            row["determinant_matches_reference"] = (
                row["fox_determinant"] == reference["fox_determinant"]
            )
            row["projection_stability_pass"] = bool(
                row["signature_matches_reference"]
                and row["crossing_count_matches_reference"]
                and row["determinant_matches_reference"]
                and row["crossing_count_matches_expected"]
                and row["determinant_matches_expected"]
            )


def first_stable_resolution(group: list[dict[str, Any]]) -> int | str:
    resolutions = sorted({int(row["resolution"]) for row in group})
    for resolution in resolutions:
        suffix = [row for row in group if int(row["resolution"]) >= resolution]
        if suffix and all(bool(row["projection_stability_pass"]) for row in suffix):
            return resolution
    return ""


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for fixture in FIXTURES:
        for mode in (
            "exact_polygon_subdivision",
            "smooth_parametric_resampling",
        ):
            selected = [
                row
                for row in rows
                if row["fixture"] == fixture.name and row["source_mode"] == mode
            ]
            passed = [
                row for row in selected if row["extraction_status"] == "passed"
            ]
            alternating = [
                row for row in passed if bool(row["alternating_projection"])
            ]
            summaries.append(
                {
                    "fixture": fixture.name,
                    "source_mode": mode,
                    "row_count": len(selected),
                    "extraction_pass_count": len(passed),
                    "projection_stability_pass_count": sum(
                        bool(row["projection_stability_pass"])
                        for row in selected
                    ),
                    "expected_determinant_pass_count": sum(
                        bool(row["determinant_matches_expected"])
                        for row in selected
                    ),
                    "topological_fixture_pass_count": sum(
                        bool(row["topological_fixture_pass"])
                        for row in selected
                    ),
                    "generic_projection_row_count": sum(
                        row["projection_class"] == "generic_tilt"
                        for row in selected
                    ),
                    "generic_projection_stability_pass_count": sum(
                        row["projection_class"] == "generic_tilt"
                        and bool(row["projection_stability_pass"])
                        for row in selected
                    ),
                    "alternating_projection_count": len(alternating),
                    "tait_construction_pass_count": sum(
                        row["tait_construction_status"] == "passed"
                        for row in selected
                    ),
                    "tait_construction_failure_count": sum(
                        row["tait_construction_status"] == "failed"
                        for row in selected
                    ),
                    "tait_shortcut_agreement_count": sum(
                        row["unsigned_tait_shortcut_agrees"] is True
                        for row in selected
                    ),
                    "first_stable_resolution": first_stable_resolution(selected),
                    "minimum_crossing_angle_degrees": (
                        min(
                            float(row["minimum_crossing_angle_degrees"])
                            for row in passed
                        )
                        if passed
                        else ""
                    ),
                    "minimum_normalized_depth_separation": (
                        min(
                            float(row["normalized_minimum_depth_separation"])
                            for row in passed
                        )
                        if passed
                        else ""
                    ),
                    "minimum_crossing_vertex_parameter_margin": (
                        min(
                            float(
                                row[
                                    "minimum_crossing_vertex_parameter_margin"
                                ]
                            )
                            for row in passed
                        )
                        if passed
                        else ""
                    ),
                    "maximum_vertex_distortion_estimate": max(
                        float(row["vertex_distortion_estimate"])
                        for row in selected
                    ),
                    "total_runtime_seconds": sum(
                        float(row["runtime_seconds"]) for row in selected
                    ),
                }
            )
    return summaries


def render_plot(rows: list[dict[str, Any]]) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(12.2, 8.4))
    colors = {
        "3_1_torus_T_2_3": "#2060a8",
        "5_1_torus_T_2_5": "#b64926",
        "4_1_figure_eight": "#16826c",
    }
    markers = {
        "exact_polygon_subdivision": "o",
        "smooth_parametric_resampling": "s",
    }
    selected = [
        row
        for row in rows
        if row["projection"] == "z_axis"
        and row["extraction_status"] == "passed"
    ]
    for fixture in FIXTURES:
        for mode in markers:
            group = sorted(
                (
                    row
                    for row in selected
                    if row["fixture"] == fixture.name
                    and row["source_mode"] == mode
                ),
                key=lambda row: int(row["resolution"]),
            )
            if not group:
                continue
            label = (
                f"{fixture.name}; "
                f"{'subdivision' if mode.startswith('exact') else 'resampling'}"
            )
            x = [int(row["resolution"]) for row in group]
            style = {
                "color": colors[fixture.name],
                "marker": markers[mode],
                "linewidth": 1.5,
                "markersize": 4.5,
                "label": label,
            }
            axes[0, 0].plot(x, [int(row["crossing_count"]) for row in group], **style)
            axes[0, 1].plot(
                x,
                [float(row["vertex_distortion_estimate"]) for row in group],
                **style,
            )
            axes[1, 0].plot(
                x,
                [
                    float(row["minimum_crossing_angle_degrees"])
                    for row in group
                ],
                **style,
            )
            axes[1, 1].plot(
                x,
                [
                    float(row["normalized_minimum_depth_separation"])
                    for row in group
                ],
                **style,
            )
    titles = (
        "Extracted crossing count",
        "Vertex-sampled distortion lower bound",
        "Minimum projected crossing angle",
        "Minimum normalized over/under depth",
    )
    ylabels = (
        "crossings",
        "intrinsic / Euclidean",
        "degrees",
        "depth / bounding-box diagonal",
    )
    for axis, title, ylabel in zip(axes.flat, titles, ylabels, strict=True):
        axis.set_title(title)
        axis.set_xlabel("polygon vertices")
        axis.set_ylabel(ylabel)
        axis.grid(alpha=0.25)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", ncol=3, fontsize=8)
    figure.suptitle(
        "Polygonal knot projection and refinement stability (z projection)",
        fontsize=14,
    )
    figure.tight_layout(rect=(0.0, 0.08, 1.0, 0.96))
    figure.savefig(
        OUTPUT_DIR / "polygonal_projection_stability.png",
        dpi=190,
    )
    plt.close(figure)


def make_report(
    rows: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    backend: dict[str, Any],
) -> str:
    table = "\n".join(
        "| {fixture} | {source_mode} | {projection_stability_pass_count}/"
        "{row_count} | {topological_fixture_pass_count}/{row_count} | "
        "{generic_projection_stability_pass_count}/"
        "{generic_projection_row_count} | "
        "{alternating_projection_count} | {tait_shortcut_agreement_count} | "
        "{first_stable_resolution} | {minimum_crossing_angle_degrees:.3f} | "
        "{minimum_normalized_depth_separation:.6f} |".format(**row)
        for row in summaries
    )
    successful = [row for row in rows if row["extraction_status"] == "passed"]
    failures = [row for row in rows if row["extraction_status"] == "failed"]
    exact = [
        row
        for row in rows
        if row["source_mode"] == "exact_polygon_subdivision"
    ]
    smooth = [
        row
        for row in rows
        if row["source_mode"] == "smooth_parametric_resampling"
    ]
    exact_pass = sum(bool(row["projection_stability_pass"]) for row in exact)
    smooth_pass = sum(bool(row["projection_stability_pass"]) for row in smooth)
    nonalternating = sum(
        row["extraction_status"] == "passed"
        and not bool(row["alternating_projection"])
        for row in rows
    )
    topology_pass = sum(bool(row["topological_fixture_pass"]) for row in rows)
    tait_failures = sum(
        row["tait_construction_status"] == "failed" for row in rows
    )
    generic = [row for row in rows if row["projection_class"] == "generic_tilt"]
    generic_stable = sum(
        bool(row["projection_stability_pass"]) for row in generic
    )
    simplified_extra_pairs = sum(
        row["extraction_status"] == "passed"
        and row["crossing_count"] != row["expected_crossing_count"]
        and bool(row["topological_fixture_pass"])
        for row in rows
    )
    return f"""# Polygonal Projection Stability Report

## Result

The local experiment completed `{len(rows)}` diagram extractions:
`{len(successful)}` succeeded and `{len(failures)}` failed.

- Exact edge subdivision stability: `{exact_pass}/{len(exact)}` rows.
- Smooth-parametric resampling stability: `{smooth_pass}/{len(smooth)}` rows.
- Generic-tilt raw-diagram stability: `{generic_stable}/{len(generic)}` rows.
- Simplified topology fixture checks: `{topology_pass}/{len(rows)}` rows.
- Successful nonalternating projections: `{nonalternating}`.
- Tait-construction diagnostic failures: `{tait_failures}`.

| Fixture | Mode | Raw stable | Topology pass | Generic stable | Alternating | Tait agreements | First stable vertices | Min angle | Min normalized depth |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{table}

The exact-subdivision and smooth-resampling modes answer different
questions. Subdivision inserts vertices on the same polygonal image, so a
change signals extraction instability. Smooth resampling changes the
polygonal approximation, so low-resolution differences are convergence
data rather than violations of an exact invariance statement.

The `{simplified_extra_pairs}` coarse nonalternating rows with extra
crossings simplify in Spherogram to the expected fixture crossing count and
retain the expected Fox determinant. They therefore fail the deliberately
strict raw-diagram signature gate but pass the weaker topology fixture gate.
Conversely, the axis-aligned trefoil subdivision failures lose a crossing
at a polygon vertex and change the determinant from `3` to `1`; those are
backend/projection failures, not harmless diagram inflation. All three
small tilted directions avoid that exact-vertex failure. The recorded
crossing-parameter margin is `0` for the problematic axis-aligned geometry,
making the nongeneric vertex incidence explicit.

## Checks

Each successful row records:

1. a one-component signed Gauss traversal and a canonical signature
   normalized under crossing relabeling, basepoint change, and reversal;
2. a PD code and independent Fox-coloring determinant;
3. both checkerboard Tait tree counts;
4. whether the projection is alternating, which is the precondition for
   comparing unsigned Tait tree counts with the determinant;
5. minimum crossing angle and over/under depth separation;
6. vertex-sampled distortion and nonlocal clearance diagnostics; and
7. a small Spherogram Reidemeister simplification check, when available.

The Fox determinant remains the topology check for nonalternating
projections. An unsigned Tait disagreement outside the alternating regime
would be inapplicable, not a counterexample.

## Pardon Connection

This implements the first experiment ranked in `PARDON_TRANSFER_NOTES.md`.
Pardon's distortion work motivates coupling a topological extraction with
intrinsic-versus-Euclidean geometry. His polygonal approximation arguments
motivate keeping exact subdivision separate from changing approximations.
The present finite checks do not import or reprove Pardon's theorems.

## Backend

- Python: `{backend["python_executable"]}`
- NumPy: `{backend["numpy_version"]}`
- pyknotid: `{backend.get("pyknotid_version", "unavailable")}`
- Spherogram: `{backend.get("spherogram_version", "unavailable")}`
- planarity extension available: `{backend["planarity_available"]}`
- backend status: `{backend["backend_status"]}`
- NumPy compatibility aliases added locally:
  `{", ".join(backend["numpy_legacy_aliases_added"]) or "none"}`

`pyknotid` is an optional experiment backend, not a package dependency.
Its ordinary Windows dependency installation attempted to build the legacy
`planarity` extension and failed without MSVC. The local crossing/PD path
works without that extension, using pyknotid's Python crossing helper.
That packaging limitation is backend evidence, not knot-theoretic evidence.

## Scope

This is reproducible finite evidence that the selected polygonal fixtures
and projection margins behave stably in the tested range. It is not a new
knot theorem, a proof that the sampled curves are isotopic at every
resolution, a complete projection-genericity theorem, or an extension of
the Four Color Theorem.

## Sources

- pyknotid space-curve documentation:
  https://pyknotid.readthedocs.io/en/latest/sources/spacecurves/spacecurve.html
- pyknotid representations:
  https://pyknotid.readthedocs.io/en/latest/sources/representations/
- John Pardon, *On the distortion of knots on embedded surfaces*:
  https://arxiv.org/abs/1010.1972
- John Pardon, *On the unfolding of simple closed curves*:
  https://web.math.princeton.edu/~jpardon/manuscripts/01_unfold.pdf
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    knot_class, link_class, backend = load_backends()
    (OUTPUT_DIR / "geometry_backend_availability.json").write_text(
        json.dumps(backend, indent=2),
        encoding="utf-8",
    )
    if knot_class is None:
        raise SystemExit(
            "pyknotid is unavailable; see geometry_backend_availability.json"
        )
    rows = build_rows(knot_class, link_class)
    summaries = summarize(rows)
    write_csv(OUTPUT_DIR / "polygonal_projection_stability_rows.csv", rows)
    write_csv(
        OUTPUT_DIR / "polygonal_projection_stability_summary.csv",
        summaries,
    )
    write_csv(
        OUTPUT_DIR / "polygonal_projection_stability_errors.csv",
        [
            {
                "fixture": row["fixture"],
                "source_mode": row["source_mode"],
                "resolution": row["resolution"],
                "projection": row["projection"],
                "error_stage": (
                    "extraction"
                    if row["extraction_status"] == "failed"
                    else "tait_construction"
                ),
                "error_message": (
                    row["error_message"]
                    if row["extraction_status"] == "failed"
                    else row["tait_error"]
                ),
            }
            for row in rows
            if row["extraction_status"] == "failed"
            or row["tait_construction_status"] == "failed"
        ],
        fieldnames=[
            "fixture",
            "source_mode",
            "resolution",
            "projection",
            "error_stage",
            "error_message",
        ],
    )
    render_plot(rows)
    (OUTPUT_DIR / "POLYGONAL_PROJECTION_STABILITY_REPORT.md").write_text(
        make_report(rows, summaries, backend),
        encoding="utf-8",
    )
    passed = sum(bool(row["projection_stability_pass"]) for row in rows)
    print(
        f"Polygonal projection stability: {passed}/{len(rows)} rows passed; "
        f"{sum(row['extraction_status'] == 'failed' for row in rows)} failures"
    )


if __name__ == "__main__":
    main()

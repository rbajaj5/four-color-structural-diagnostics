"""Audit real-valued volume and graph diagnostics for small prime knots."""

from __future__ import annotations

import csv
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from four_color_diagnostics.knot_volume import (
    REGULAR_IDEAL_TETRAHEDRON_VOLUME,
    invariant_collision_rows,
    normalized_simplicial_volume,
    prime_knot_volume_fixtures,
)
from four_color_diagnostics.tait import (
    fox_coloring_determinant,
    tait_graphs_from_pd_code,
)


OUTPUT_DIR = ROOT / "results"


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
        for name in ("spherogram", "snappy", "regina", "sageall")
    }
    return {
        "python_executable": sys.executable,
        "python_version": sys.version,
        **{f"{name}_available": available for name, available in modules.items()},
        "sage_command_available": shutil.which("sage") is not None,
        "volume_policy": (
            "Use SnapPy numerical volume only after the fixture geometry and "
            "numerical solution type agree. Mark rigorous verification "
            "unavailable when Sage interval arithmetic is absent."
        ),
        "v3": REGULAR_IDEAL_TETRAHEDRON_VOLUME,
    }


def correlation(rows: list[dict[str, Any]], key: str) -> float:
    x = np.asarray([float(row[key]) for row in rows], dtype=float)
    y = np.asarray(
        [float(row["jsj_hyperbolic_volume_numeric"]) for row in rows],
        dtype=float,
    )
    if len(x) < 2 or float(np.std(x)) == 0.0:
        return math.nan
    return float(np.corrcoef(x, y)[0, 1])


def collect_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    if not audit["spherogram_available"] or not audit["snappy_available"]:
        raise RuntimeError("Spherogram and SnapPy are required for this gate")

    import snappy
    from spherogram import Link

    audit["snappy_version"] = getattr(snappy, "__version__", "unknown")
    rows = []
    for fixture in prime_knot_volume_fixtures():
        link = Link(fixture.name)
        pd_code = tuple(
            tuple(int(value) for value in crossing)
            for crossing in link.PD_code()
        )
        determinant = fox_coloring_determinant(pd_code)
        pair = tait_graphs_from_pd_code(pd_code)
        first_spectrum = pair.first.laplacian_spectrum()
        second_spectrum = pair.second.laplacian_spectrum()
        alternating = bool(link.is_alternating())
        first_trees = pair.first.spanning_tree_count()
        second_trees = pair.second.spanning_tree_count()
        unsigned_tait_matches = first_trees == second_trees == determinant

        manifold = snappy.Manifold(fixture.name)
        numerical_volume = float(manifold.volume())
        solution_type = str(manifold.solution_type())
        numerical_hyperbolic = (
            numerical_volume > 1e-10
            and solution_type == "all tetrahedra positively oriented"
        )
        geometry_gate_passed = (
            fixture.expected_geometry == "hyperbolic" and numerical_hyperbolic
        ) or (
            fixture.expected_geometry == "torus"
            and abs(numerical_volume) <= 1e-10
        )

        verification_status = "not_attempted_for_nonhyperbolic_fixture"
        verification_error = ""
        verified_hyperbolic = False
        if fixture.expected_geometry == "hyperbolic":
            try:
                verified_hyperbolic = bool(manifold.verify_hyperbolicity()[0])
                verification_status = (
                    "verified" if verified_hyperbolic else "verification_failed"
                )
            except Exception as error:
                verification_status = "unavailable"
                verification_error = f"{type(error).__name__}: {error}"

        jsj_volume = (
            numerical_volume if fixture.expected_geometry == "hyperbolic" else 0.0
        )
        simplicial_volume = normalized_simplicial_volume(
            (jsj_volume,) if jsj_volume else ()
        )
        isometry_signature = ""
        if numerical_hyperbolic:
            try:
                isometry_signature = str(manifold.isometry_signature())
            except Exception:
                isometry_signature = ""

        rows.append(
            {
                "knot_name": fixture.name,
                "prime_table_fixture": True,
                "crossing_count": fixture.crossing_count,
                "component_count": len(link.link_components),
                "alternating_diagram": alternating,
                "expected_geometry": fixture.expected_geometry,
                "torus_type": fixture.torus_type,
                "canonical_real_volume_kind": "JSJ_hyperbolic_piece_volume",
                "snappy_volume_numeric": numerical_volume,
                "jsj_hyperbolic_volume_numeric": jsj_volume,
                "normalized_simplicial_volume_numeric": simplicial_volume,
                "snappy_solution_type": solution_type,
                "numerically_hyperbolic": numerical_hyperbolic,
                "verified_hyperbolic": verified_hyperbolic,
                "verification_status": verification_status,
                "verification_error": verification_error,
                "geometry_gate_passed": geometry_gate_passed,
                "isometry_signature_unverified": isometry_signature,
                "fox_determinant": determinant,
                "log_fox_determinant": math.log(determinant),
                "first_tait_vertex_count": pair.first.vertex_count,
                "second_tait_vertex_count": pair.second.vertex_count,
                "first_tait_tree_count": first_trees,
                "second_tait_tree_count": second_trees,
                "unsigned_tait_determinant_applicable": alternating,
                "unsigned_tait_matches_fox": unsigned_tait_matches,
                "first_tait_algebraic_connectivity": (
                    first_spectrum[1] if len(first_spectrum) > 1 else 0.0
                ),
                "second_tait_algebraic_connectivity": (
                    second_spectrum[1] if len(second_spectrum) > 1 else 0.0
                ),
                "maximum_tait_spectral_radius": max(
                    first_spectrum[-1],
                    second_spectrum[-1],
                ),
                "volume_per_crossing": jsj_volume / fixture.crossing_count,
            }
        )
    return rows


def summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    buckets = [
        ("all", rows),
        (
            "hyperbolic",
            [row for row in rows if row["expected_geometry"] == "hyperbolic"],
        ),
        (
            "torus",
            [row for row in rows if row["expected_geometry"] == "torus"],
        ),
        ("alternating", [row for row in rows if row["alternating_diagram"]]),
        (
            "nonalternating",
            [row for row in rows if not row["alternating_diagram"]],
        ),
    ]
    for bucket, members in buckets:
        volumes = [float(row["jsj_hyperbolic_volume_numeric"]) for row in members]
        summaries.append(
            {
                "bucket": bucket,
                "row_count": len(members),
                "geometry_gate_passed": sum(
                    bool(row["geometry_gate_passed"]) for row in members
                ),
                "verified_hyperbolic_count": sum(
                    bool(row["verified_hyperbolic"]) for row in members
                ),
                "minimum_volume": min(volumes),
                "mean_volume": float(np.mean(volumes)),
                "maximum_volume": max(volumes),
                "mean_normalized_simplicial_volume": float(
                    np.mean(
                        [
                            float(row["normalized_simplicial_volume_numeric"])
                            for row in members
                        ]
                    )
                ),
                "unsigned_tait_applicable_count": sum(
                    bool(row["unsigned_tait_determinant_applicable"])
                    for row in members
                ),
            }
        )
    return summaries


def render_plot(rows: list[dict[str, Any]]) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12.0, 5.0))
    colors = [
        "#1976d2" if row["expected_geometry"] == "hyperbolic" else "#d32f2f"
        for row in rows
    ]
    axes[0].scatter(
        [row["fox_determinant"] for row in rows],
        [row["jsj_hyperbolic_volume_numeric"] for row in rows],
        c=colors,
        alpha=0.85,
    )
    axes[0].set_xlabel("Fox determinant")
    axes[0].set_ylabel("JSJ hyperbolic volume")
    axes[0].set_title("Equal determinants need not imply equal volume")
    axes[0].grid(alpha=0.25)

    hyperbolic = [
        row for row in rows if row["expected_geometry"] == "hyperbolic"
    ]
    axes[1].scatter(
        [row["maximum_tait_spectral_radius"] for row in hyperbolic],
        [row["jsj_hyperbolic_volume_numeric"] for row in hyperbolic],
        c="#2e7d32",
        alpha=0.85,
    )
    axes[1].set_xlabel("Maximum checkerboard spectral radius")
    axes[1].set_ylabel("Hyperbolic volume")
    axes[1].set_title("Graph spectrum is a diagnostic, not a volume formula")
    axes[1].grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "prime_knot_volume_diagnostics.png", dpi=190)
    plt.close(figure)


def make_report(
    rows: list[dict[str, Any]],
    collisions: list[dict[str, Any]],
    audit: dict[str, Any],
) -> str:
    hyperbolic = [
        row for row in rows if row["expected_geometry"] == "hyperbolic"
    ]
    torus = [row for row in rows if row["expected_geometry"] == "torus"]
    collision_table = "\n".join(
        "| {fox_determinant} | {knot_names} | {geometry_types} | {volumes} | "
        "{volume_range:.6g} |".format(**row)
        for row in sorted(
            collisions,
            key=lambda row: float(row["volume_range"]),
            reverse=True,
        )[:12]
    )
    correlations = {
        "crossing_count": correlation(hyperbolic, "crossing_count"),
        "log_fox_determinant": correlation(
            hyperbolic,
            "log_fox_determinant",
        ),
        "maximum_tait_spectral_radius": correlation(
            hyperbolic,
            "maximum_tait_spectral_radius",
        ),
    }
    return f"""# Prime Knot Real-Volume Gate

## Answer

Not every prime knot has a positive hyperbolic volume. The finite fixtures
show the distinction directly:

- `{len(hyperbolic)}` hyperbolic prime-knot fixtures have positive numerical
  complement volumes.
- `{len(torus)}` torus-knot fixtures have no hyperbolic complement structure
  and contribute zero JSJ hyperbolic volume.
- Every fixture still receives a nonnegative real-valued generalized
  quantity: the sum of its hyperbolic JSJ-piece volumes. Dividing that sum
  by `v3 = {REGULAR_IDEAL_TETRAHEDRON_VOLUME:.16g}` gives the normalized
  simplicial volume.

Satellite prime knots are not present in this through-eight-crossing gate.
For them, the same generalized quantity requires a certified JSJ
decomposition and summation over only the hyperbolic pieces.

## Finite Gate

- Named prime knots processed: `{len(rows)}`
- Crossing range: `3-8`
- Geometry checks matching the registry:
  `{sum(bool(row["geometry_gate_passed"]) for row in rows)}`
- Rigorous interval hyperbolicity verifications:
  `{sum(bool(row["verified_hyperbolic"]) for row in rows)}`
- SnapPy available: `{audit["snappy_available"]}`
- Sage available:
  `{audit["sage_command_available"] or audit["sageall_available"]}`

The positive volumes in this report are numerical SnapPy values, not
interval-certified values, because the installed standalone SnapPy reports
that rigorous verification requires Sage.

## Determinant Collisions

| Determinant | Knots | Geometry | Volumes | Range |
| ---: | --- | --- | --- | ---: |
{collision_table}

In particular, `4_1` and `5_1` both have determinant `5`, but their
generalized volumes are approximately `2.0298832128` and `0`. Likewise,
`5_2` and `7_1` both have determinant `7`, with volumes approximately
`2.8281220883` and `0`. Determinant and checkerboard spectra therefore do
not determine geometric volume.

## Finite Correlations

On the `{len(hyperbolic)}` hyperbolic rows:

- crossing count versus volume: `{correlations["crossing_count"]:.6f}`
- log determinant versus volume: `{correlations["log_fox_determinant"]:.6f}`
- maximum checkerboard spectral radius versus volume:
  `{correlations["maximum_tait_spectral_radius"]:.6f}`

These are descriptive correlations on a small table, not knot theorems.

## Relation to the Matrix Counterexample

The matrix note and this gate share a methodological lesson, not a claimed
formula. A local matrix term can violate a proposed bound while the complete
permutation average is rescued by cancellation. Here, determinant and Tait
spectra retain exact projection information while failing to determine the
global geometric volume. In both settings, local or compressed invariants
must be checked against the complete aggregate object.

## Sources

- SnapPy volume and verification documentation:
  https://snappy.computop.org/manifold.html
- SnapPy verified computations:
  https://snappy.computop.org/verify.html
- Murakami and Murakami, colored Jones polynomials and simplicial volume:
  https://arxiv.org/abs/math/9905075
- Murakami, introduction to the Volume Conjecture:
  https://arxiv.org/abs/1002.0126
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audit = backend_audit()
    rows = collect_rows(audit)
    collisions = invariant_collision_rows(
        rows,
        invariant_key="fox_determinant",
        volume_key="jsj_hyperbolic_volume_numeric",
    )
    summaries = summary_rows(rows)

    write_csv(OUTPUT_DIR / "prime_knot_volume_rows.csv", rows)
    write_csv(OUTPUT_DIR / "prime_knot_volume_collisions.csv", collisions)
    write_csv(OUTPUT_DIR / "prime_knot_volume_summary.csv", summaries)
    (OUTPUT_DIR / "prime_knot_volume_backend.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    render_plot(rows)
    (OUTPUT_DIR / "PRIME_KNOT_VOLUME_REPORT.md").write_text(
        make_report(rows, collisions, audit),
        encoding="utf-8",
    )
    print(
        f"Processed {len(rows)} prime-knot fixtures; "
        f"wrote {len(collisions)} determinant collision groups."
    )


if __name__ == "__main__":
    main()

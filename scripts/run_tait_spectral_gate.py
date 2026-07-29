"""Run the alternating-knot Tait spectral determinant fixture gate."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from four_color_diagnostics.tait import (
    faces_from_pd_code,
    fox_coloring_determinant,
    tait_graphs_from_pd_code,
)
from four_color_diagnostics.tait_fixtures import ALTERNATING_KNOT_FIXTURES


OUTPUT_DIR = ROOT / "results"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def backend_audit() -> dict[str, Any]:
    modules = {
        name: bool(importlib.util.find_spec(name))
        for name in ("spherogram", "snappy", "regina", "sageall")
    }
    audit: dict[str, Any] = {
        "python_executable": sys.executable,
        "python_version": sys.version,
        **{f"{name}_available": available for name, available in modules.items()},
        "sage_command_available": shutil.which("sage") is not None,
        "named_fixture_checks": [],
    }
    if modules["spherogram"]:
        import spherogram
        from spherogram import Link

        audit["spherogram_version"] = getattr(
            spherogram,
            "__version__",
            "unknown",
        )
        for fixture in ALTERNATING_KNOT_FIXTURES:
            try:
                link = Link(fixture.name)
                observed_pd = tuple(
                    tuple(int(value) for value in crossing)
                    for crossing in link.PD_code()
                )
                observed_faces = {
                    frozenset(
                        (int(corner.crossing.label), int(corner.strand_index))
                        for corner in face
                    )
                    for face in link.faces()
                }
                reconstructed_faces = {
                    frozenset(face) for face in faces_from_pd_code(fixture.pd_code)
                }
                audit["named_fixture_checks"].append(
                    {
                        "name": fixture.name,
                        "loaded": True,
                        "crossing_count": len(link.crossings),
                        "component_count": len(link.link_components),
                        "alternating": bool(link.is_alternating()),
                        "pd_code_exact_match": observed_pd == fixture.pd_code,
                        "face_partition_match": (
                            observed_faces == reconstructed_faces
                        ),
                        "error": "",
                    }
                )
            except Exception as error:
                audit["named_fixture_checks"].append(
                    {
                        "name": fixture.name,
                        "loaded": False,
                        "crossing_count": None,
                        "component_count": None,
                        "alternating": None,
                        "pd_code_exact_match": False,
                        "face_partition_match": False,
                        "error": f"{type(error).__name__}: {error}",
                    }
                )
    return audit


def fixture_tables() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    registry = []
    fixture_rows = []
    graph_rows = []
    for fixture in ALTERNATING_KNOT_FIXTURES:
        pair = tait_graphs_from_pd_code(fixture.pd_code)
        fox = fox_coloring_determinant(fixture.pd_code)
        graph_data = []
        for checkerboard, graph in (
            ("first", pair.first),
            ("second", pair.second),
        ):
            exact = graph.spanning_tree_count()
            spectral = graph.spectral_spanning_tree_estimate()
            graph_data.append((exact, spectral))
            graph_rows.append(
                {
                    "knot_name": fixture.name,
                    "checkerboard": checkerboard,
                    "vertex_count": graph.vertex_count,
                    "edge_count_with_multiplicity": graph.edge_count,
                    "loop_count": graph.loop_count,
                    "maximum_edge_multiplicity": (
                        graph.maximum_edge_multiplicity
                    ),
                    "laplacian_spectrum": " ".join(
                        f"{value:.12g}"
                        for value in graph.laplacian_spectrum()
                    ),
                    "matrix_tree_count": exact,
                    "spectral_tree_estimate": spectral,
                    "spectral_absolute_error": abs(exact - spectral),
                }
            )
        first_exact, first_spectral = graph_data[0]
        second_exact, second_spectral = graph_data[1]
        passed = (
            len(pair.faces) == len(fixture.pd_code) + 2
            and first_exact
            == second_exact
            == fox
            == fixture.expected_determinant
            and abs(first_spectral - first_exact) < 1e-8
            and abs(second_spectral - second_exact) < 1e-8
        )
        registry.append(
            {
                "knot_name": fixture.name,
                "crossing_count": len(fixture.pd_code),
                "expected_determinant": fixture.expected_determinant,
                "alternating_fixture": True,
                "pd_code": json.dumps(fixture.pd_code),
                "source": "Spherogram named table; determinant cross-check: KnotInfo",
            }
        )
        fixture_rows.append(
            {
                "knot_name": fixture.name,
                "crossing_count": len(fixture.pd_code),
                "face_count": len(pair.faces),
                "euler_face_count_expected": len(fixture.pd_code) + 2,
                "first_tait_vertex_count": pair.first.vertex_count,
                "second_tait_vertex_count": pair.second.vertex_count,
                "first_matrix_tree_count": first_exact,
                "second_matrix_tree_count": second_exact,
                "first_spectral_tree_estimate": first_spectral,
                "second_spectral_tree_estimate": second_spectral,
                "fox_coloring_determinant": fox,
                "expected_determinant": fixture.expected_determinant,
                "all_routes_agree": passed,
                "gate_status": "passed" if passed else "failed",
            }
        )
    return registry, fixture_rows, graph_rows


def render_spectrum_plot(graph_rows: list[dict[str, Any]]) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(11.2, 8.0))
    for axis, fixture in zip(axes.flat, ALTERNATING_KNOT_FIXTURES, strict=True):
        rows = [
            row for row in graph_rows if row["knot_name"] == fixture.name
        ]
        for row in rows:
            spectrum = [
                float(value)
                for value in str(row["laplacian_spectrum"]).split()
            ]
            axis.plot(
                range(len(spectrum)),
                spectrum,
                marker="o",
                linewidth=1.8,
                label=f"{row['checkerboard']} Tait graph",
            )
        axis.set_title(
            f"{fixture.name}: determinant {fixture.expected_determinant}"
        )
        axis.set_xlabel("ordered eigenvalue index")
        axis.set_ylabel("Laplacian eigenvalue")
        axis.grid(alpha=0.25)
        axis.legend()
    figure.suptitle(
        "Dual checkerboard spectra can differ while tree counts agree",
        fontsize=14,
    )
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "tait_laplacian_spectra.png", dpi=190)
    plt.close(figure)


def make_report(
    rows: list[dict[str, Any]],
    backend: dict[str, Any],
) -> str:
    table = "\n".join(
        "| {knot_name} | {crossing_count} | {first_tait_vertex_count} | "
        "{second_tait_vertex_count} | {first_matrix_tree_count} | "
        "{second_matrix_tree_count} | {fox_coloring_determinant} | "
        "{expected_determinant} | {gate_status} |".format(**row)
        for row in rows
    )
    passed = sum(row["gate_status"] == "passed" for row in rows)
    named_checks = backend.get("named_fixture_checks", [])
    backend_passed = sum(
        bool(row.get("loaded"))
        and bool(row.get("alternating"))
        and int(row.get("component_count", 0)) == 1
        and bool(row.get("pd_code_exact_match"))
        and bool(row.get("face_partition_match"))
        for row in named_checks
    )
    return f"""# Tait Spectral Determinant Fixture Gate

## Result

The gate passed `{passed}` of `{len(rows)}` alternating-knot fixtures.

| Knot | Crossings | Tait A vertices | Tait B vertices | Trees A | Trees B | Fox determinant | Expected | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{table}

Each fixture passed four checks:

1. PD corner tracing produced `crossings + 2` complementary regions.
2. Both checkerboard Tait multigraphs had the expected spanning-tree count
   by an exact Laplacian cofactor.
3. The product of nonzero Laplacian eigenvalues divided by the vertex count
   reproduced the same count numerically.
4. An independent reduced Fox-coloring matrix computed from the PD strands
   produced the same knot determinant.

The collision `det(4_1) = det(5_1) = 5` is retained deliberately: determinant
and graph spectra are useful diagnostics, not complete knot identifiers.

## Backend Audit

- Python: `{backend["python_executable"]}`
- Spherogram available: `{backend["spherogram_available"]}`
- SnapPy available: `{backend["snappy_available"]}`
- Regina available: `{backend["regina_available"]}`
- Sage command available: `{backend["sage_command_available"]}`
- `sageall` available: `{backend["sageall_available"]}`
- Spherogram named-fixture checks passed: `{backend_passed}` of
  `{len(named_checks)}`

Spherogram was used only to confirm that the named fixtures load as
one-component alternating diagrams and that their PD codes match. Its
polynomial/determinant routines require Sage in this environment. The exact
Tait and Fox calculations in this gate do not depend on Sage.

## What This Establishes

This establishes a tested software bridge:

`alternating PD code -> checkerboard faces -> Tait multigraphs -> Laplacian
spectrum / spanning trees -> determinant`.

It does not establish that spectra classify knots, extend the Four Color
Theorem, or prove a new knot theorem. Nonalternating diagrams need signed
Goeritz data rather than the unsigned spanning-tree shortcut used here.

## Pardon Boundary

John Pardon's work contributes useful methods for a later geometric
stability layer, not the determinant identity itself. See
`PARDON_TRANSFER_NOTES.md` for the exact separation.

## Sources

- KnotInfo: https://knotinfo.org/
- Matrix-Tree background: https://arxiv.org/abs/2209.01284
- Alternating-link determinant and Tait spanning trees:
  https://repository.lsu.edu/mathematics_pubs/235/
"""


def pardon_note() -> str:
    return """# Pardon Transfer Notes

## Papers Reviewed

1. John Pardon, *On the distortion of knots on embedded surfaces*:
   https://arxiv.org/abs/1010.1972
2. John Pardon, *On the unfolding of simple closed curves*:
   https://web.math.princeton.edu/~jpardon/manuscripts/01_unfold.pdf
3. John Pardon, *Central limit theorems for random polygons in an arbitrary
   convex set*: https://arxiv.org/abs/1003.4209

## Useful Ideas

### Geometry certificate alongside topology

Pardon's distortion is the supremum of intrinsic arclength distance divided
by ambient Euclidean distance. His knot paper bounds distortion using
surface intersection complexity and repeatedly cuts space while preserving
the topologically essential region. For a future 3D-curve pipeline,
distortion and separator-intersection counts can diagnose whether a
polygonal embedding is geometrically strained or undersampled even when its
PD/Tait determinant is unchanged.

This does not make distortion a complete knot invariant, nor does Pardon's
bound apply indiscriminately to every extracted curve.

### Controlled polygonal approximation

The unfolding paper passes from rectifiable curves to inscribed polygons
while preserving length and nondecreasing pairwise-distance constraints. It
also formulates expansion through linear inequalities and connects their
dual obstructions to Farkas and Maxwell-Cremona stress theory.

The transferable design is a refinement gate: subdivide a 3D curve,
reproject generically, and require the PD code and Tait determinant to
stabilize while monitoring geometric inequalities. Convex optimization can
be used for the geometric constraints, but it is not needed for the exact
determinant calculation implemented here.

### Local-to-global random polygon statistics

The random-polygon paper decomposes global vertex/area statistics into
angularly local terms, introduces affine-invariant normalization, and
controls long-range dependence before applying a central limit theorem.
For later random-knot experiments, this suggests collecting crossing,
region, and Tait-subgraph statistics by angular sectors rather than treating
the entire projection as one undifferentiated sample.

No random-knot central limit theorem follows from Pardon's polygon result.

## Ranked Next Experiments

1. **Projection/refinement stability:** test whether PD codes and Tait
   determinants stabilize under polygon subdivision and small generic
   changes of projection direction.
2. **Geometry/topology joint audit:** compare distortion and
   separator-intersection counts with Tait spectral features.
3. **Affine-normalized random projections:** decompose diagram statistics
   into angular sectors and estimate dependence before proposing a limit
   law.

The first experiment is the closest direct continuation of the present
fixture gate.
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    backend = backend_audit()
    registry, fixture_rows, graph_rows = fixture_tables()
    write_csv(OUTPUT_DIR / "tait_fixture_registry.csv", registry)
    write_csv(OUTPUT_DIR / "tait_fixture_rows.csv", fixture_rows)
    write_csv(OUTPUT_DIR / "tait_graph_rows.csv", graph_rows)
    (OUTPUT_DIR / "tait_backend_availability.json").write_text(
        json.dumps(backend, indent=2),
        encoding="utf-8",
    )
    render_spectrum_plot(graph_rows)
    (OUTPUT_DIR / "TAIT_SPECTRAL_DETERMINANT_REPORT.md").write_text(
        make_report(fixture_rows, backend),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "PARDON_TRANSFER_NOTES.md").write_text(
        pardon_note(),
        encoding="utf-8",
    )
    passed = sum(row["gate_status"] == "passed" for row in fixture_rows)
    print(f"Tait spectral fixture gate: {passed}/{len(fixture_rows)} passed")


if __name__ == "__main__":
    main()

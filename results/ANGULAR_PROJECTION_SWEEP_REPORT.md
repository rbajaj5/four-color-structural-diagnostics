# Angular Projection Sweep Report

## Result

The sweep tested `128` deterministic Fibonacci-sphere
directions on each of three `96`-vertex polygonal knots,
for `384` total rows.

- Extraction failures: `0`.
- Fox-determinant mismatches: `0`.
- Rows not reduced to the minimal fixture by the bounded simplifier:
  `173`.

| Fixture | Extracted | Determinant | Raw minimal | Simplified fixture | Alternating | Min crossings | Max crossings | Min angle | Min vertex margin |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3_1_torus_T_2_3 | 128/128 | 128/128 | 62/128 | 98/128 | 62 | 3 | 9 | 1.5425 | 0.000234214 |
| 5_1_torus_T_2_5 | 128/128 | 128/128 | 17/128 | 56/128 | 17 | 5 | 18 | 1.5657 | 8.09874e-05 |
| 4_1_figure_eight | 128/128 | 128/128 | 35/128 | 57/128 | 35 | 4 | 19 | 1.4270 | 0.00027779 |

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
| 3_1_torus_T_2_3 | raw_minimal | 62 | 3.000 | 53.822 | 0.05215 | 0.23208 |
| 3_1_torus_T_2_3 | extra_simplified_to_fixture | 36 | 6.333 | 27.277 | 0.02744 | 0.20166 |
| 3_1_torus_T_2_3 | extra_unresolved_by_basic_simplifier | 30 | 5.500 | 34.824 | 0.02473 | 0.22740 |
| 5_1_torus_T_2_5 | raw_minimal | 17 | 5.000 | 58.028 | 0.04923 | 0.20980 |
| 5_1_torus_T_2_5 | extra_simplified_to_fixture | 39 | 6.231 | 44.491 | 0.03864 | 0.15165 |
| 5_1_torus_T_2_5 | extra_unresolved_by_basic_simplifier | 72 | 11.181 | 23.684 | 0.01906 | 0.14163 |
| 4_1_figure_eight | raw_minimal | 35 | 4.000 | 32.158 | 0.06163 | 0.16386 |
| 4_1_figure_eight | extra_simplified_to_fixture | 22 | 9.955 | 22.654 | 0.02089 | 0.14406 |
| 4_1_figure_eight | extra_unresolved_by_basic_simplifier | 71 | 11.042 | 27.081 | 0.01842 | 0.14018 |

Across these fixtures, raw-minimal directions have larger mean crossing
angles and larger median crossing-to-vertex margins than directions with
extra crossings. This is a descriptive finite-sample pattern, not a proof
that either margin controls diagram complexity.

## Backend

- Python: `C:\Users\anaxe\AppData\Local\Programs\Python\Python312\python.exe`
- pyknotid: `0.5.3`
- Spherogram: `2.4.1`
- planarity extension available: `False`

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

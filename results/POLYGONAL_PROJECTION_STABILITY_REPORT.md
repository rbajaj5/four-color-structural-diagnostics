# Polygonal Projection Stability Report

## Result

The local experiment completed `120` diagram extractions:
`120` succeeded and `0` failed.

- Exact edge subdivision stability: `46/48` rows.
- Smooth-parametric resampling stability: `70/72` rows.
- Generic-tilt raw-diagram stability: `88/90` rows.
- Simplified topology fixture checks: `118/120` rows.
- Successful nonalternating projections: `4`.
- Tait-construction diagnostic failures: `0`.

| Fixture | Mode | Raw stable | Topology pass | Generic stable | Alternating | Tait agreements | First stable vertices | Min angle | Min normalized depth |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3_1_torus_T_2_3 | exact_polygon_subdivision | 14/16 | 14/16 | 12/12 | 14 | 14 |  | 28.106 | 0.245494 |
| 3_1_torus_T_2_3 | smooth_parametric_resampling | 24/24 | 24/24 | 18/18 | 24 | 24 | 16 | 28.106 | 0.217587 |
| 5_1_torus_T_2_5 | exact_polygon_subdivision | 16/16 | 16/16 | 12/12 | 16 | 16 | 32 | 54.593 | 0.216348 |
| 5_1_torus_T_2_5 | smooth_parametric_resampling | 24/24 | 24/24 | 18/18 | 24 | 24 | 16 | 54.058 | 0.142799 |
| 4_1_figure_eight | exact_polygon_subdivision | 16/16 | 16/16 | 12/12 | 16 | 16 | 32 | 12.379 | 0.191935 |
| 4_1_figure_eight | smooth_parametric_resampling | 22/24 | 24/24 | 16/18 | 22 | 22 | 32 | 0.116 | 0.136832 |

The exact-subdivision and smooth-resampling modes answer different
questions. Subdivision inserts vertices on the same polygonal image, so a
change signals extraction instability. Smooth resampling changes the
polygonal approximation, so low-resolution differences are convergence
data rather than violations of an exact invariance statement.

The `2` coarse nonalternating rows with extra
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

- Python: `C:\Users\anaxe\AppData\Local\Programs\Python\Python312\python.exe`
- NumPy: `2.4.2`
- pyknotid: `0.5.3`
- Spherogram: `2.4.1`
- planarity extension available: `False`
- backend status: `available`
- NumPy compatibility aliases added locally:
  `float, int, complex`

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

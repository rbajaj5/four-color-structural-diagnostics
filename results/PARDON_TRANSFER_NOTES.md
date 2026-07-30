# Pardon Transfer Notes

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

1. **Geometry/topology joint audit:** compare distortion and
   separator-intersection counts with Tait spectral features.
2. **Projection-margin certification:** replace empirical angular/depth
   margins with interval-certified crossing persistence where practical.
3. **Affine-normalized random projections:** extend the deterministic
   angular sweep with affine normalization and dependence estimates before
   proposing a limit law.

The original first-ranked projection/refinement experiment is implemented
by `run_polygonal_projection_stability.py`. Its finite results separate
exact subdivision, smooth resampling, generic projection tilts, and
Reidemeister simplification.

`run_angular_projection_sweep.py` implements a finite deterministic
precursor to the third item. It samples 128 Fibonacci-sphere directions per
fixture and buckets raw-minimal, simplifiable, and unresolved diagrams by
their angular and vertex-incidence margins. It does not establish a random
projection limit theorem.

# Four Color Structural Diagnostics

This repository turns a Four Color special-case dictionary into an
executable, certificate-producing solver hierarchy for finite planar graphs.

The solver:

1. validates planarity;
2. handles edgeless and bipartite graphs directly;
3. uses the triangle-free planar theorem for non-bipartite triangle-free
   graphs;
4. uses the even-degree criterion for sphere triangulations;
5. decomposes articulation-rich graphs into biconnected blocks and glues
   their certificates by color permutation;
6. asks the fixed 3-color question for the remaining planar cores; and
7. emits and directly verifies a proper coloring certificate.

For sphere triangulations, the implementation also constructs the planar
dual and checks that dual bipartiteness agrees with the primal even-degree
criterion before using the parity shortcut.

For the last branch, a failed 3-color decision and the Four Color Theorem
give exact chromatic number four. This is the useful algorithmic distinction
behind Or Zamir's *k-Coloring is Faster than Computing the Chromatic Number*:
fixed-palette decision can be preferable to computing unrestricted
chromatic number. The finite implementation here uses exact DSATUR, not
Zamir's randomized asymptotic algorithm.

## Results

Run:

```bash
python -m pip install -e ".[test]"
python -m pytest -q
python scripts/run_structural_benchmark.py
python scripts/run_atlas_audit.py
python scripts/run_spectral_partition_audit.py
python scripts/run_tait_spectral_gate.py
python scripts/run_prime_knot_volume_gate.py  # optional SnapPy backend
python scripts/run_polygonal_projection_stability.py  # optional backend
python scripts/run_angular_projection_sweep.py  # optional backend
```

Generated artifacts:

- `results/structural_benchmark_rows.csv`
- `results/coloring_certificates.json`
- `results/structural_search_comparison.png`
- `results/STRUCTURAL_DIAGNOSTIC_REPORT.md`
- `results/atlas_audit_rows.csv`
- `results/atlas_audit_summary_by_route.csv`
- `results/atlas_route_distribution.png`
- `results/atlas_block_savings_distribution.png`
- `results/ATLAS_EXHAUSTIVE_AUDIT_REPORT.md`
- `results/atlas_block_decomposition_outcomes.csv`
- `results/STRUCTURE_RANDOMNESS_ADAPTATION.md`
- `results/spectral_partition_rows.csv`
- `results/spectral_partition_summary.csv`
- `results/spectral_block_outcome_features.csv`
- `results/spectral_feature_correlations.csv`
- `results/spectral_composition_checks.csv`
- `results/spectral_stress_partition_rows.csv`
- `results/spectral_partition_comparison.png`
- `results/spectral_gain_scatter.png`
- `results/SPECTRAL_PARTITION_REPORT.md`
- `results/tait_fixture_registry.csv`
- `results/tait_fixture_rows.csv`
- `results/tait_graph_rows.csv`
- `results/tait_backend_availability.json`
- `results/tait_laplacian_spectra.png`
- `results/TAIT_SPECTRAL_DETERMINANT_REPORT.md`
- `results/prime_knot_volume_rows.csv`
- `results/prime_knot_volume_collisions.csv`
- `results/prime_knot_volume_summary.csv`
- `results/prime_knot_volume_backend.json`
- `results/prime_knot_volume_diagnostics.png`
- `results/PRIME_KNOT_VOLUME_REPORT.md`
- `results/prime_knot_length_spectrum_rows.csv`
- `results/prime_knot_short_geodesic_records.csv`
- `results/prime_knot_length_spectrum_summary.csv`
- `results/prime_knot_length_spectrum_collisions.csv`
- `results/prime_knot_length_spectrum_errors.csv`
- `results/prime_knot_length_spectrum_backend.json`
- `results/prime_knot_length_spectrum_diagnostics.png`
- `results/PRIME_KNOT_LENGTH_SPECTRUM_REPORT.md`
- `results/PARDON_ANOSOV_TRANSFER_NOTES.md`
- `results/PARDON_TRANSFER_NOTES.md`
- `results/geometry_backend_availability.json`
- `results/polygonal_projection_stability_rows.csv`
- `results/polygonal_projection_stability_summary.csv`
- `results/polygonal_projection_stability_errors.csv`
- `results/polygonal_projection_stability.png`
- `results/POLYGONAL_PROJECTION_STABILITY_REPORT.md`
- `results/angular_projection_sweep_rows.csv`
- `results/angular_projection_sweep_summary.csv`
- `results/angular_projection_margin_buckets.csv`
- `results/angular_projection_sweep_errors.csv`
- `results/angular_projection_sweep.png`
- `results/ANGULAR_PROJECTION_SWEEP_REPORT.md`

The benchmark includes a `10`, `26`, `50`, and `82` vertex size ladder of
compactified checkerboard and one-diagonal-flip triangulations. It directly
exercises the exact three-to-four-color parity transition used in the
related curvature-map work and measures the failed 3-color search avoided
by the parity certificate.

An independent direct-assignment enumerator also audits all 1,015 nonempty
planar graphs in the NetworkX graph atlas through seven vertices. It agrees
with the structural hierarchy on all 1,015 and validates every emitted
coloring edge by edge. The audit baseline does not call the DSATUR solver.
The block layer saves 1,010 theorem-directed search nodes in aggregate on
this domain, while the emitted outcome table also preserves the 42
per-instance regressions.

The spectral audit compares true connected components, one-vertex
articulation separators, Fiedler sign/median cuts, and a balanced BFS
baseline. It verifies direct-sum and one-vertex coalescence characteristic
polynomial identities exactly on symbolic fixtures. On the atlas,
Fiedler-median cuts use fewer boundary edges than equally balanced BFS cuts,
but block count and articulation count have stronger finite associations
with search-node savings than the spectral features tested.

## Independent Matrix-Analysis Note

The repository also carries a self-contained
[exact certificate](research_notes/zhang_conjecture_4_1/README.md) for a
two-dimensional counterexample to Conjecture 4.1 in Teng Zhang's
*A Note on the Matrix Arithmetic-Geometric Mean Inequality*. Four
rank-one positive semidefinite projectors violate the stated operator-norm
bound by the exact ratio \(1+\sqrt2\). Adding \(tI\) to each matrix gives a
strictly positive-definite counterexample for an exact nonzero interval of
\(t\). Exact expansion also shows that cancellation among all 24 ordered
products preserves the full four-matrix Recht-Re average inequality on this
entire family, despite failure of the proposed termwise estimate.

This note is mathematically independent of the Four Color experiments.
Its exact calculation is verified in CI; its literature priority is not
claimed. A bounded search record is included beside the certificate.

## Scope

This is proof-guided finite software. It is not:

- a new proof or strengthening of the Four Color Theorem;
- an implementation of Zamir's research algorithm;
- evidence for an asymptotic DSATUR improvement;
- a formal proof derived from the finite graph-atlas audit;
- a weighted routing or integrality theorem; or
- a knot invariant; or
- a theorem that every polygonal approximation or projection is stable.

For later knot work, the report records the precise alternating-diagram
bridge through Tait-graph spanning-tree counts and the Matrix-Tree Theorem;
the fixture gate now implements that bridge for `3_1`, `4_1`, `5_1`, and
`5_2`. Both checkerboard graphs, their Laplacian spectra, and an independent
Fox-coloring determinant agree with the expected values. The retained
`det(4_1) = det(5_1)` collision demonstrates that this is not a knot
classifier.

`PARDON_TRANSFER_NOTES.md` reviews three precise ideas for the subsequent
geometry layer: distortion and intersection counts, polygonal refinement
under geometric inequalities, and affine-invariant local decompositions for
random polygon statistics. None is claimed to prove the Tait identity.

The first Pardon-inspired geometry experiment is now implemented. It
extracts Gauss/PD data from polygonal `3_1`, `5_1`, and `4_1` embeddings
under exact edge subdivision, smooth resampling, and four projection
directions. The strict raw-diagram gate passes 116 of 120 rows; a small
Spherogram simplification gate passes 118 of 120. Two coarse figure-eight
projections add a removable crossing pair, whereas an exactly axis-aligned
trefoil projection exposes a pyknotid vertex-crossing failure at high
subdivision. All tested small generic tilts avoid that trefoil failure.

`pyknotid` and Spherogram are optional local experiment backends rather than
core dependencies. The script writes an explicit backend audit and exits if
`pyknotid` is unavailable. This keeps the exact graph and Tait test suite
portable across the Python versions used in CI.

The prime-knot volume gate covers all 35 named prime knots through eight
crossings. It separates ordinary hyperbolic volume from the generalized
sum of hyperbolic JSJ-piece volumes, which is zero for the four torus-knot
fixtures. Exact Fox determinants and checkerboard spectra are retained
beside the numerical geometric values. Equal-determinant pairs such as
`4_1`/`5_1` and `5_2`/`7_1` have different volumes, demonstrating that
these graph-derived invariants do not determine complement geometry.

The follow-on short-length-spectrum gate processes all 31 hyperbolic
fixtures numerically through real-length cutoff `3.0`. It records
orientation-independent length ratios, multiplicity-weighted short-length
spread, finite geodesic-count growth, and complex-holonomy angle sectors.
A fixed-alpha leave-one-out comparison shows that adding only the shortest
geodesic reduces volume-prediction RMSE by 5.25% relative to crossing
count, log determinant, and maximum Tait spectral radius. Adding the full
12-feature local/angular stack slightly worsens held-out error. All 15
hyperbolic equal-determinant pairs have distinct five-record finite
fingerprints in this census, but the fingerprints are numerical, unmarked,
cutoff-dependent diagnostics rather than complete invariants.

The higher-Teichmuller analogy is deliberately limited. Pressure metrics
use full marked length spectra for Anosov representations, whereas cusped
knot-complement holonomy has parabolics and belongs near relative Anosov
theory. The gate computes neither a pressure metric nor a rigorous entropy.
Its use of normalized local sectors transfers a statistical design pattern
from Pardon's random-polygon work, not Pardon's central limit theorem.

A deterministic 128-direction Fibonacci-sphere audit then broadens the
projection check. All 384 extracted diagrams retain the fixture's Fox
determinant, while raw crossing counts vary from `3-9`, `5-18`, and `4-19`
for the three fixtures. Minimal diagrams occupy only a subset of directions;
their crossing-angle and crossing-to-vertex margins are larger on average
than those of extra-crossing views. The bounded simplifier is explicitly
treated as incomplete, so an unresolved diagram is not called a different
knot.

NetworkX supplies planarity recognition. Every emitted coloring certificate
is checked independently against every edge.

## Sources

- Robertson, Sanders, Seymour, and Thomas, Four Color materials:
  https://thomas.math.gatech.edu/FC/fourcolor.html
- Or Zamir, *k-Coloring is Faster than Computing the Chromatic Number*:
  https://arxiv.org/abs/2607.25973
- Tsai and West, *A New Proof of 3-Colorability of Eulerian
  Triangulations*: https://dwest.web.illinois.edu/pubs/eultri.pdf
- NetworkX graph atlas documentation:
  https://networkx.org/documentation/stable/reference/generated/networkx.generators.atlas.graph_atlas_g.html
- Alweiss, Bowen, and Sabok, *Sums, products, and exponents in
  two-colorings of the naturals*: https://arxiv.org/abs/2512.09598
- Matrix-Tree Theorem background: https://arxiv.org/abs/2209.01284
- Alternating-link determinant and Tait spanning trees:
  https://repository.lsu.edu/mathematics_pubs/235/
- Teng Zhang, *A Note on the Matrix Arithmetic-Geometric Mean Inequality*:
  https://arxiv.org/abs/1411.5058
- Lai and Lim, *Recht-Re Noncommutative Arithmetic-Geometric Mean
  Conjecture is False*: https://arxiv.org/abs/2006.01510
- SnapPy volume and verified-computation documentation:
  https://snappy.computop.org/verify.html
- Murakami and Murakami, *The Colored Jones Polynomials and the Simplicial
  Volume of a Knot*: https://arxiv.org/abs/math/9905075
- Pardon, *Central limit theorems for random polygons in an arbitrary
  convex set*: https://arxiv.org/abs/1003.4209
- Guichard and Wienhard, *Anosov representations: Domains of discontinuity
  and applications*: https://arxiv.org/abs/1108.0733
- Bridgeman, Canary, Labourie, and Sambarino, *The pressure metric for
  Anosov representations*: https://arxiv.org/abs/1301.7459
- Weisman, *An extended definition of Anosov representation for relatively
  hyperbolic groups*: https://arxiv.org/abs/2205.07183

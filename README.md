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
- `results/PARDON_TRANSFER_NOTES.md`

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

## Scope

This is proof-guided finite software. It is not:

- a new proof or strengthening of the Four Color Theorem;
- an implementation of Zamir's research algorithm;
- evidence for an asymptotic DSATUR improvement;
- a formal proof derived from the finite graph-atlas audit;
- a weighted routing or integrality theorem; or
- a knot invariant.

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

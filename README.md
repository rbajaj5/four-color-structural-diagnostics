# Four Color Structural Diagnostics

This repository turns a Four Color special-case dictionary into an
executable, certificate-producing solver hierarchy for finite planar graphs.

The solver:

1. validates planarity;
2. handles edgeless and bipartite graphs directly;
3. uses the triangle-free planar theorem for non-bipartite triangle-free
   graphs;
4. uses the even-degree criterion for sphere triangulations;
5. asks the fixed 3-color question for the remaining planar graphs; and
6. emits and directly verifies a proper coloring certificate.

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
```

Generated artifacts:

- `results/structural_benchmark_rows.csv`
- `results/coloring_certificates.json`
- `results/structural_search_comparison.png`
- `results/STRUCTURAL_DIAGNOSTIC_REPORT.md`
- `results/atlas_audit_rows.csv`
- `results/atlas_audit_summary_by_route.csv`
- `results/atlas_route_distribution.png`
- `results/ATLAS_EXHAUSTIVE_AUDIT_REPORT.md`

The benchmark includes a `10`, `26`, `50`, and `82` vertex size ladder of
compactified checkerboard and one-diagonal-flip triangulations. It directly
exercises the exact three-to-four-color parity transition used in the
related curvature-map work and measures the failed 3-color search avoided
by the parity certificate.

An independent direct-assignment enumerator also audits all 1,015 nonempty
planar graphs in the NetworkX graph atlas through seven vertices. It agrees
with the structural hierarchy on all 1,015 and validates every emitted
coloring edge by edge. The audit baseline does not call the DSATUR solver.

## Scope

This is proof-guided finite software. It is not:

- a new proof or strengthening of the Four Color Theorem;
- an implementation of Zamir's research algorithm;
- evidence for an asymptotic DSATUR improvement;
- a formal proof derived from the finite graph-atlas audit;
- a weighted routing or integrality theorem; or
- a knot invariant.

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

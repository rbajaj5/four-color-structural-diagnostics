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
```

Generated artifacts:

- `results/structural_benchmark_rows.csv`
- `results/coloring_certificates.json`
- `results/structural_search_comparison.png`
- `results/STRUCTURAL_DIAGNOSTIC_REPORT.md`

The benchmark includes a `10`, `26`, `50`, and `82` vertex size ladder of
compactified checkerboard and one-diagonal-flip triangulations. It directly
exercises the exact three-to-four-color parity transition used in the
related curvature-map work and measures the failed 3-color search avoided
by the parity certificate.

## Scope

This is proof-guided finite software. It is not:

- a new proof or strengthening of the Four Color Theorem;
- an implementation of Zamir's research algorithm;
- evidence for an asymptotic DSATUR improvement;
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

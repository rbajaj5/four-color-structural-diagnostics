# Spectral Partition Audit

## Question

Can several graph partitions clarify when a structural Four Color diagnostic
decomposes cleanly, and can spectral features help explain the finite
block-decomposition gains and regressions already observed?

## Partition Comparison

| Method | Graphs | Nontrivial | Mean cut edges | Mean balance | Mean spectral-union error | Zero-error cases |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| articulation_separator | 546 | 546 | 3.885 | 0.378 | 0.458043 | 0 |
| bfs_balanced | 774 | 774 | 5.243 | 0.781 | 0.574737 | 0 |
| connected_components | 1015 | 240 | 0.000 | 0.836 | 0.000000 | 1015 |
| fiedler_median | 774 | 774 | 3.859 | 0.781 | 0.473430 | 0 |
| fiedler_sign | 774 | 774 | 3.084 | 0.627 | 0.378062 | 0 |

Connected components have mean spectral-union error
`0.000000` because the
adjacency and Laplacian matrices are block diagonal. Fiedler-median
partitioning discarded `3.859` edges on
average, compared with `5.243` for the balanced
BFS baseline, a `26.4%` mean reduction at the same
part-size balance. These cuts are heuristic decompositions: their
induced-part spectra are not the original graph spectrum.

Articulation-separator partitions are exact as graph separators
(`residual_cross_edge_count = 0` after deleting the separator), but their
blocks share a boundary vertex. They therefore require a gluing identity,
not a direct multiset union.

## Exact Composition Checks

All `5` of `5` exact symbolic fixtures passed. The
checks cover two disjoint unions and three one-vertex coalescences, including
K4-C5, K4-K4, and wheel-path examples. Coefficients from both sides are
preserved in `spectral_composition_checks.csv`.

## Existing Search Outcome

| Block outcome | Graphs | Mean nodes saved | Mean articulations | Mean algebraic connectivity | Mean Fiedler cut |
| --- | ---: | ---: | ---: | ---: | ---: |
| improved | 472 | 2.288 | 1.176 | 0.494 | 3.638 |
| regressed | 42 | -1.667 | 1.214 | 0.659 | 2.730 |
| tied | 501 | 0.000 | 0.441 | 1.168 | 4.129 |

The strongest finite associations were:

| Feature | Graphs | Pearson | Spearman |
| --- | ---: | ---: | ---: |
| biconnected_block_count | 1015 | 0.395 | 0.499 |
| algebraic_connectivity | 1015 | -0.382 | -0.457 |
| articulation_count | 1015 | 0.362 | 0.444 |
| fiedler_sign_cut_edges | 774 | -0.279 | -0.327 |
| adjacency_energy | 1015 | -0.111 | -0.242 |
| edge_count | 1015 | -0.162 | -0.232 |

These are descriptive associations on the 1,015 nonempty planar graphs in
the NetworkX atlas through seven vertices. They are not a runtime theorem,
causal explanation, or train/test predictive claim.

## Articulation-Chain Stress Test

| Fixture | Vertices | Fiedler cut edges | Balance | Algebraic connectivity |
| --- | ---: | ---: | ---: | ---: |
| articulation_k4_chain_4 | 13 | 3 | 0.857 | 0.329378 |
| articulation_k4_chain_8 | 25 | 3 | 0.923 | 0.093049 |
| articulation_k4_chain_16 | 49 | 3 | 0.960 | 0.024543 |

On the K4 articulation-chain ladder, the balanced Fiedler cut consistently
found the three-edge neck while algebraic connectivity fell as the chain
grew. This detects the global bottleneck, but does not remove the local
coloring overhead that caused the previously recorded large-chain
block-decomposition regressions. The spectrum is therefore useful
diagnostically without replacing the exact block-cut certificate logic.

## Knot-Theory Bridge

For a reduced alternating knot diagram, the determinant can be read as the
number of spanning trees of a checkerboard (Tait) graph. The Matrix-Tree
Theorem in turn expresses that count through nonzero Laplacian eigenvalues.
That gives a precise later bridge from graph spectra to knot data. This
repository has not yet parsed knot diagrams or claimed that a graph spectrum
is a complete knot invariant.

## Scope

- True connected components obey direct-sum spectral composition.
- One-vertex block gluings obey the checked coalescence polynomial identity.
- Fiedler and BFS cuts are empirical partition strategies only.
- Cospectral nonisomorphic graphs remain possible.
- No strengthening of the Four Color Theorem or new knot theorem is claimed.

## Sources

- Matrix-Tree Theorem background: https://arxiv.org/abs/2209.01284
- Alternating-link determinant and Tait spanning trees:
  https://repository.lsu.edu/mathematics_pubs/235/
- Characteristic polynomials of coalescence graphs:
  https://www.sciencedirect.com/book/9780128020685/spectral-radius-of-graphs

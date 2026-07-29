# Structural Planar Coloring Diagnostic Report

## Result

The executable hierarchy produced valid exact coloring certificates for all
28 fixtures. It used `1425` DSATUR search nodes after
structural preprocessing, compared with `1727` for blind
increasing-palette search, saving `302` nodes on this finite benchmark.

| Fixture | V | E | chi | Certified route | Generic nodes | Structural nodes | Saved |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| edgeless_8 | 8 | 0 | 1 | edgeless | 9 | 0 | 9 |
| path_8 | 8 | 7 | 2 | bipartite | 10 | 0 | 10 |
| odd_cycle_7 | 7 | 7 | 3 | triangle_free_non_bipartite | 15 | 8 | 7 |
| octahedral | 6 | 12 | 3 | eulerian_sphere_triangulation | 10 | 7 | 3 |
| tetrahedral_K4 | 4 | 6 | 4 | non_eulerian_sphere_triangulation | 12 | 5 | 7 |
| wheel_6 | 6 | 10 | 4 | generic_planar_three_color_no | 18 | 15 | 3 |
| wheel_7 | 7 | 12 | 3 | generic_planar_three_color_yes | 11 | 8 | 3 |
| grid_4x4 | 16 | 24 | 2 | bipartite | 18 | 0 | 18 |
| compactified_checkerboard_2 | 10 | 24 | 3 | eulerian_sphere_triangulation | 14 | 11 | 3 |
| compactified_one_flip_2 | 10 | 24 | 4 | non_eulerian_sphere_triangulation | 18 | 11 | 7 |
| compactified_checkerboard_4 | 26 | 72 | 3 | eulerian_sphere_triangulation | 30 | 27 | 3 |
| compactified_one_flip_4 | 26 | 72 | 4 | non_eulerian_sphere_triangulation | 58 | 27 | 31 |
| compactified_checkerboard_6 | 50 | 144 | 3 | eulerian_sphere_triangulation | 54 | 51 | 3 |
| compactified_one_flip_6 | 50 | 144 | 4 | non_eulerian_sphere_triangulation | 104 | 51 | 53 |
| compactified_checkerboard_8 | 82 | 240 | 3 | eulerian_sphere_triangulation | 86 | 83 | 3 |
| compactified_one_flip_8 | 82 | 240 | 4 | non_eulerian_sphere_triangulation | 166 | 83 | 83 |
| compactified_seeded_4_7 | 26 | 72 | 4 | non_eulerian_sphere_triangulation | 38 | 27 | 11 |
| compactified_seeded_4_19 | 26 | 72 | 4 | non_eulerian_sphere_triangulation | 55 | 44 | 11 |
| compactified_seeded_6_7 | 50 | 144 | 4 | non_eulerian_sphere_triangulation | 519 | 508 | 11 |
| compactified_seeded_6_19 | 50 | 144 | 4 | non_eulerian_sphere_triangulation | 60 | 51 | 9 |
| compactified_seeded_8_7 | 82 | 240 | 4 | non_eulerian_sphere_triangulation | 109 | 98 | 11 |
| compactified_seeded_8_19 | 82 | 240 | 4 | non_eulerian_sphere_triangulation | 94 | 83 | 11 |
| stacked_triangulation_12 | 12 | 30 | 4 | non_eulerian_sphere_triangulation | 20 | 13 | 7 |
| stacked_triangulation_24 | 24 | 66 | 4 | non_eulerian_sphere_triangulation | 32 | 25 | 7 |
| stacked_triangulation_48 | 48 | 138 | 4 | non_eulerian_sphere_triangulation | 56 | 49 | 7 |
| articulation_k4_chain_4 | 13 | 24 | 4 | block_decomposition | 21 | 20 | 1 |
| articulation_k4_chain_8 | 25 | 48 | 4 | block_decomposition | 33 | 40 | -7 |
| articulation_k4_chain_16 | 49 | 96 | 4 | block_decomposition | 57 | 80 | -23 |

## Routes

- `bipartite`: 2
- `block_decomposition`: 3
- `edgeless`: 1
- `eulerian_sphere_triangulation`: 5
- `generic_planar_three_color_no`: 1
- `generic_planar_three_color_yes`: 1
- `non_eulerian_sphere_triangulation`: 14
- `triangle_free_non_bipartite`: 1

The compactified checkerboard and one-flip size ladder exercises the exact
Eulerian/non-Eulerian sphere-triangulation transition at `10`, `26`, `50`,
and `82` vertices. On the one-flip branch, parity recognition avoids the
failed 3-color search: measured savings grow from
`7` nodes at
`V=10` to
`83` nodes at
`V=82`. This is a finite workload observation,
not an asymptotic bound. The other fixtures cover edgeless, bipartite,
triangle-free non-bipartite, and generic planar branches.

The expanded workload adds `12` deterministic irregular-grid,
stacked-triangulation, and articulation-chain fixtures. The primal
even-degree test agreed with an explicitly constructed dual-graph
bipartiteness test on all
`19` sphere triangulations. This is a redundant structural
check, independent of the final edge-by-edge coloring verification.

The K4 articulation chains deliberately expose the decomposition tradeoff.
Their search-node differences were
`1, -7, -23`:
local certificate gluing is exact, but repeated dense blocks can cost more
search nodes than a single global DSATUR traversal.

## Algorithmic Interpretation

For an arbitrary planar graph that is not settled structurally, exact
chromatic diagnosis requires a fixed 3-color decision. A YES result gives
the remaining three-color case; a NO result combines with Four Color to
give `chi=4`. Or Zamir's 2026 theorem supplies a randomized
`O*((2-epsilon_3)^n)` existence result for the generic fixed-palette
fallback. This repository uses exact DSATUR for small finite certificates;
it does not implement Zamir's algorithm.

## Claim Boundary

This is a proof-guided solver and finite workload comparison. It is not a
new proof of the Four Color Theorem, a new asymptotic coloring algorithm, or
evidence that the measured DSATUR savings persist on arbitrary graph
families. NetworkX supplies planarity recognition; the emitted coloring is
checked directly on every edge.

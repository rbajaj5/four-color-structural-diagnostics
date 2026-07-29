# Structural Planar Coloring Diagnostic Report

## Result

The executable hierarchy produced valid exact coloring certificates for all
16 fixtures. It used `387` DSATUR search nodes after
structural preprocessing, compared with `633` for blind
increasing-palette search, saving `246` nodes on this finite benchmark.

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

## Routes

- `bipartite`: 2
- `edgeless`: 1
- `eulerian_sphere_triangulation`: 5
- `generic_planar_three_color_no`: 1
- `generic_planar_three_color_yes`: 1
- `non_eulerian_sphere_triangulation`: 5
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

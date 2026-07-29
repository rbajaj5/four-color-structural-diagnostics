# Exhaustive Small-Planar-Graph Audit

## Result

The structural hierarchy agreed with a separate direct assignment enumerator
on `1015` of `1015` nonempty planar graphs in the NetworkX
graph atlas, covering every unlabeled graph through seven vertices that the
atlas marks planar. It emitted `1015` valid edge-by-edge
coloring certificates and the independent checker examined `636,594`
assignments in total.

| Diagnostic route | Graphs | Exact matches | Valid certificates | Direct assignments | Search nodes saved |
| --- | ---: | ---: | ---: | ---: | ---: |
| bipartite | 137 | 137 | 137 | 3101 | 0 |
| block_decomposition | 532 | 532 | 532 | 358495 | 1010 |
| edgeless | 7 | 7 | 7 | 7 | 0 |
| eulerian_sphere_triangulation | 2 | 2 | 2 | 185 | 0 |
| generic_planar_three_color_no | 110 | 110 | 110 | 193704 | 0 |
| generic_planar_three_color_yes | 210 | 210 | 210 | 67348 | 0 |
| non_eulerian_sphere_triangulation | 8 | 8 | 8 | 11285 | 0 |
| triangle_free_non_bipartite | 9 | 9 | 9 | 2469 | 0 |

There were `0` disagreements. For the `10`
sphere triangulations in this exhaustive range, primal even-degree parity
agreed with independently constructed dual-graph bipartiteness in
`10` cases.

Across the atlas, block decomposition reduced theorem-directed DSATUR work
from `7,878` to `6,868` search nodes, saving
`1,010` nodes. This compares the same solver with
the decomposition layer disabled and enabled; it is a finite workload
measurement rather than an asymptotic guarantee.
The decomposition improved `472` graphs, tied on `501`, and
regressed on `42`; the worst observed regression was
`4` additional nodes.

## Independence

The audit baseline enumerates fixed-palette assignments directly and checks
every edge. It does not call the repository's DSATUR solver. The structural
path and baseline still share graph parsing and Python/NetworkX process
state, so this is an independent algorithmic cross-check rather than an
independent formal proof.

NetworkX version: `3.6.1`.
Atlas definition:
https://networkx.org/documentation/stable/reference/generated/networkx.generators.atlas.graph_atlas_g.html

## Claim Boundary

This exhausts the finite NetworkX atlas through seven vertices, not all
planar graphs. Zero disagreements are evidence against implementation errors
on that domain; they do not prove the Four Color Theorem, validate an
asymptotic runtime claim, or establish correctness beyond the audited range.

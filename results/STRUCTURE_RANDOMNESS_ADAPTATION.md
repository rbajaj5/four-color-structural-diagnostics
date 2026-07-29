# Structure-versus-Residual Adaptation Note

## Source Idea

Alweiss, Bowen, and Sabok organize their arithmetic-coloring proofs by first
obtaining a relaxed monochromatic pattern, separating structured and
pseudorandom regimes, and then using the information in either regime to
control an additional term:

https://arxiv.org/abs/2512.09598

Their theorems concern two-colorings of the natural numbers and
sum/product/exponent patterns. They do not imply a graph-coloring result.

## Exact Graph Adaptation

The transferable object is the proof architecture:

1. Detect the structured regime using articulation vertices and the
   block-cut forest.
2. Diagnose each biconnected block independently.
3. Treat biconnected blocks as the residual cores requiring the existing
   theorem hierarchy or fixed three-color decision.
4. Upgrade local certificates to a global certificate by permuting colors
   at each shared articulation vertex.

The upgrade is exact because distinct blocks meet in at most one articulation
vertex and the chromatic number of a graph is the maximum over its blocks.
The final coloring is still checked against every original edge.

## Finite Evidence

On the 1,015 nonempty planar graphs in the NetworkX atlas through seven
vertices, `532` graphs used block decomposition. The layer reduced
the same theorem-directed solver from `7,878` to
`6,868` search nodes, a net saving of
`1,010`, with zero chromatic-number disagreements
against the independent direct enumerator.

## Boundary

This is an algorithmic adaptation inspired by the paper's organization, not
an application of its syndetic/thick-set machinery. The finite net saving is
not an asymptotic complexity theorem, and per-instance regressions remain.

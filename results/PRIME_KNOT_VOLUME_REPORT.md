# Prime Knot Real-Volume Gate

## Answer

Not every prime knot has a positive hyperbolic volume. The finite fixtures
show the distinction directly:

- `31` hyperbolic prime-knot fixtures have positive numerical
  complement volumes.
- `4` torus-knot fixtures have no hyperbolic complement structure
  and contribute zero JSJ hyperbolic volume.
- Every fixture still receives a nonnegative real-valued generalized
  quantity: the sum of its hyperbolic JSJ-piece volumes. Dividing that sum
  by `v3 = 1.014941606409654` gives the normalized
  simplicial volume.

Satellite prime knots are not present in this through-eight-crossing gate.
For them, the same generalized quantity requires a certified JSJ
decomposition and summation over only the hyperbolic pieces.

## Finite Gate

- Named prime knots processed: `35`
- Crossing range: `3-8`
- Geometry checks matching the registry:
  `35`
- Rigorous interval hyperbolicity verifications:
  `0`
- SnapPy available: `True`
- Sage available:
  `False`

The positive volumes in this report are numerical SnapPy values, not
interval-certified values, because the installed standalone SnapPy reports
that rigorous verification requires Sage.

## Determinant Collisions

| Determinant | Knots | Geometry | Volumes | Range |
| ---: | --- | --- | --- | ---: |
| 7 | 5_2 7_1 | hyperbolic torus | 2.82812208833 0 | 2.82812 |
| 13 | 6_3 7_3 8_1 | hyperbolic | 5.69302109128 4.59212569703 3.42720524627 | 2.26582 |
| 5 | 4_1 5_1 | hyperbolic torus | 2.02988321282 0 | 2.02988 |
| 15 | 7_4 8_21 | hyperbolic | 5.13794120187 6.78371351984 | 1.64577 |
| 19 | 7_6 8_4 | hyperbolic | 7.08492595351 5.50048641635 | 1.58444 |
| 17 | 7_5 8_2 8_3 | hyperbolic | 6.44353738085 4.93524267828 5.2386841008 | 1.50829 |
| 11 | 6_2 7_2 | hyperbolic | 4.40083251612 3.33174423164 | 1.06909 |
| 9 | 6_1 8_20 | hyperbolic | 3.16396322888 4.12490325181 | 0.96094 |
| 21 | 7_7 8_5 | hyperbolic | 7.64337517236 6.99718914779 | 0.646186 |
| 23 | 8_6 8_7 | hyperbolic | 7.47523742951 7.0221965891 | 0.453041 |
| 29 | 8_12 8_13 | hyperbolic | 8.93585692749 8.53123220146 | 0.404625 |
| 27 | 8_10 8_11 | hyperbolic | 8.65114855802 8.28631681781 | 0.364832 |

In particular, `4_1` and `5_1` both have determinant `5`, but their
generalized volumes are approximately `2.0298832128` and `0`. Likewise,
`5_2` and `7_1` both have determinant `7`, with volumes approximately
`2.8281220883` and `0`. Determinant and checkerboard spectra therefore do
not determine geometric volume.

## Finite Correlations

On the `31` hyperbolic rows:

- crossing count versus volume: `0.625372`
- log determinant versus volume: `0.950029`
- maximum checkerboard spectral radius versus volume:
  `-0.371766`

These are descriptive correlations on a small table, not knot theorems.

## Relation to the Matrix Counterexample

The matrix note and this gate share a methodological lesson, not a claimed
formula. A local matrix term can violate a proposed bound while the complete
permutation average is rescued by cancellation. Here, determinant and Tait
spectra retain exact projection information while failing to determine the
global geometric volume. In both settings, local or compressed invariants
must be checked against the complete aggregate object.

## Sources

- SnapPy volume and verification documentation:
  https://snappy.computop.org/manifold.html
- SnapPy verified computations:
  https://snappy.computop.org/verify.html
- Murakami and Murakami, colored Jones polynomials and simplicial volume:
  https://arxiv.org/abs/math/9905075
- Murakami, introduction to the Volume Conjecture:
  https://arxiv.org/abs/1002.0126

# Tait Spectral Determinant Fixture Gate

## Result

The gate passed `4` of `4` alternating-knot fixtures.

| Knot | Crossings | Tait A vertices | Tait B vertices | Trees A | Trees B | Fox determinant | Expected | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 3_1 | 3 | 3 | 2 | 3 | 3 | 3 | 3 | passed |
| 4_1 | 4 | 3 | 3 | 5 | 5 | 5 | 5 | passed |
| 5_1 | 5 | 5 | 2 | 5 | 5 | 5 | 5 | passed |
| 5_2 | 5 | 4 | 3 | 7 | 7 | 7 | 7 | passed |

Each fixture passed four checks:

1. PD corner tracing produced `crossings + 2` complementary regions.
2. Both checkerboard Tait multigraphs had the expected spanning-tree count
   by an exact Laplacian cofactor.
3. The product of nonzero Laplacian eigenvalues divided by the vertex count
   reproduced the same count numerically.
4. An independent reduced Fox-coloring matrix computed from the PD strands
   produced the same knot determinant.

The collision `det(4_1) = det(5_1) = 5` is retained deliberately: determinant
and graph spectra are useful diagnostics, not complete knot identifiers.

## Backend Audit

- Python: `C:\Users\anaxe\AppData\Local\Programs\Python\Python312\python.exe`
- Spherogram available: `True`
- SnapPy available: `True`
- Regina available: `False`
- Sage command available: `False`
- `sageall` available: `False`
- Spherogram named-fixture checks passed: `4` of
  `4`

Spherogram was used only to confirm that the named fixtures load as
one-component alternating diagrams and that their PD codes match. Its
polynomial/determinant routines require Sage in this environment. The exact
Tait and Fox calculations in this gate do not depend on Sage.

## What This Establishes

This establishes a tested software bridge:

`alternating PD code -> checkerboard faces -> Tait multigraphs -> Laplacian
spectrum / spanning trees -> determinant`.

It does not establish that spectra classify knots, extend the Four Color
Theorem, or prove a new knot theorem. Nonalternating diagrams need signed
Goeritz data rather than the unsigned spanning-tree shortcut used here.

## Pardon Boundary

John Pardon's work contributes useful methods for a later geometric
stability layer, not the determinant identity itself. See
`PARDON_TRANSFER_NOTES.md` for the exact separation.

## Sources

- KnotInfo: https://knotinfo.org/
- Matrix-Tree background: https://arxiv.org/abs/2209.01284
- Alternating-link determinant and Tait spanning trees:
  https://repository.lsu.edu/mathematics_pubs/235/

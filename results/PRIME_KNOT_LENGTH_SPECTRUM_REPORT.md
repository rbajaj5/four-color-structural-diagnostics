# Prime-Knot Short Length-Spectrum Gate

## Result

The gate processed all `31` hyperbolic prime knots through eight
crossings using numerical SnapPy complex lengths below `3.0`.
Every knot produced at least five grouped records. `7` knots
needed a randomized triangulation after the initial Dirichlet construction
failed; all retries and messages are preserved.

The minimal Pardon/Anosov-inspired geometric augmentation
`did` improve fixed-alpha
leave-one-out RMSE, while the complete local/angular stack
`did not`:

| Model | Features | RMSE | MAE | Better rows | Sign-test p |
| --- | ---: | ---: | ---: | ---: | ---: |
| determinant/Tait baseline | 3 | 0.346484 | 0.266021 | - | - |
| + shortest geodesic | 4 | 0.328291 | 0.265458 | 13/31 | 0.473130 |
| + shortest geodesic and local spread | 5 | 0.341402 | 0.261922 | 16/31 | 1.000000 |
| full local/angular stack | 12 | 0.347400 | 0.272845 | 13/31 | 0.473130 |

The shortest-geodesic RMSE improvement is
`0.018194`
(`5.25%`).
The full-stack change is
`-0.000916`. Reporting all four
nested models prevents the favorable shortest-geodesic result from hiding
the fact that the larger feature stack adds no held-out benefit. These are
descriptive finite-census results, not theorems or selected production
models.

The exact paired sign test also blocks a stronger claim: the
shortest-geodesic model improves absolute error on only
`13` of
`31` non-tied rows
(`p = 0.473130`). Its RMSE gain
comes from the magnitude of a minority of corrections, not consistent
row-wise superiority.

## Precise Statistics

Correlations with numerical hyperbolic volume:

- `short_length_cv`: correlation `-0.870440`
- `systole_numeric`: correlation `0.749077`
- `second_to_first_length_ratio`: correlation `-0.483933`
- `finite_counting_entropy_proxy`: correlation `0.449469`
- `twist_angle_resultant`: correlation `0.337623`
- `twist_angle_entropy_8bin`: correlation `-0.219477`
- `geodesic_count_le_2_5`: correlation `-0.054169`

The statistics include the shortest real length, a scale-free second/first
length ratio, multiplicity-weighted coefficient of variation, counts below
three fixed cutoffs, a finite count-growth slope, and eight-sector
twist-angle entropy/resultant. The count-growth slope is **not** the
topological entropy of the geodesic flow.

## Determinant Collisions

The hyperbolic census contains `15` equal-determinant
knot pairs. Their five-record scale-free short-spectrum fingerprints agree
in `0` cases. The smallest pairwise fingerprint
distance is `1.16873`.

This says the finite numerical statistic separates these particular
determinant collisions. It does not make the fingerprint a complete knot
invariant, and rounded equality is not a proof of isospectrality.

## What This Adds to Pardon and Wienhard

Pardon's useful contribution here is the architecture of a precise
local-to-global statistic: normalize first, retain angular sectors, and
test concentration rather than reducing an object to one scalar. The
experiment evaluates that architecture on complex lengths; it does not
improve or alter Pardon's random-polygon or knot-distortion theorems.

The Anosov connection is similarly disciplined. Full marked length spectra,
entropy, and pressure are central in higher Teichmuller theory. These knot
complements are cusped and have parabolics, so the relevant bridge is
relative Anosov theory, not an assertion that the ordinary knot holonomy is
an Anosov representation. This gate computes no pressure metric.

## Backend and Limits

- SnapPy: `3.3.2`
- Sage available:
  `False`
- recovered Dirichlet failures: `11`
- status of every spectrum: `numerical_unverified`
- spectrum cutoff: `3.0`

The finite cutoff, unmarked spectrum, table-size selection, and lack of
interval certification prevent a novelty or universality claim. The next
mathematically serious step is a marked or relative length-spectrum
construction, not adding more ad hoc regressors.

## Sources

- Pardon, random polygons: https://arxiv.org/abs/1003.4209
- Pardon, knot distortion: https://arxiv.org/abs/1010.1972
- Guichard and Wienhard, Anosov representations:
  https://arxiv.org/abs/1108.0733
- Bridgeman, Canary, Labourie, and Sambarino, pressure metric:
  https://arxiv.org/abs/1301.7459
- Weisman, relative Anosov representations:
  https://arxiv.org/abs/2205.07183
- SnapPy numerical length spectra:
  https://snappy.computop.org/manifold.html

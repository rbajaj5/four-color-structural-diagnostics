# Exact Certificate for Zhang's Conjecture 4.1

## Status

This note gives an exact counterexample to Conjecture 4.1 in Teng Zhang,
*A Note on the Matrix Arithmetic-Geometric Mean Inequality*,
Electronic Journal of Linear Algebra 34 (2018), 283-287.

The mathematical calculation is exact and machine-checked. The literature
priority claim is deliberately weaker: a bounded search performed on
2026-07-29 did not locate this counterexample, but that search is not an
exhaustive priority review.

The conjecture asks whether positive semidefinite matrices always satisfy

\[
\|A(BC+CB)D+D(BC+CB)A\|
\leq \frac{1}{64}\|A+B+C+D\|^4.
\]

## Counterexample

Take the four rank-one orthogonal projectors

\[
A=\begin{pmatrix}1&0\\0&0\end{pmatrix},\quad
B=\begin{pmatrix}0&0\\0&1\end{pmatrix},
\]

\[
C=\frac12\begin{pmatrix}1&-1\\-1&1\end{pmatrix},\quad
D=\frac12\begin{pmatrix}1&1\\1&1\end{pmatrix}.
\]

They are real symmetric positive semidefinite matrices and

\[
A+B+C+D=2I.
\]

Direct multiplication gives

\[
X=A(BC+CB)D+D(BC+CB)A
=\begin{pmatrix}-\frac12&-\frac14\\-\frac14&0\end{pmatrix}.
\]

The eigenvalues of \(X\) are

\[
\frac{-1-\sqrt2}{4},\qquad \frac{-1+\sqrt2}{4}.
\]

Therefore

\[
\|X\|=\frac{1+\sqrt2}{4}
>\frac14
=\frac1{64}\|2I\|^4.
\]

The exact violation ratio is \(1+\sqrt2\).

## Positive-Definite Family

The failure is not confined to singular matrices. Replace every projector
\(M\) above by \(M_t=M+tI\). All four matrices are positive definite when
\(t>0\). The two eigenvalues of the new left-hand expression are

\[
\lambda_\pm(t)=\frac{2t+1}{4}
\left(8t^3+12t^2+2t-1\pm\sqrt2\right).
\]

Let \(\rho\) be the unique positive solution of

\[
16\rho^3+24\rho^2+8\rho=\sqrt2.
\]

Numerically, \(\rho=0.1255393107918237\ldots\). For
\(0\leq t<\rho\), the exact gap between the operator norm and the
conjectured upper bound is

\[
\frac{2t+1}{4}
\left(\sqrt2-16t^3-24t^2-8t\right)>0.
\]

Thus every \(0<t<\rho\) supplies a strictly positive-definite
counterexample. At \(t=1/10\), the left-hand matrix is

\[
\begin{pmatrix}
-627/1250&-3/10\\
-3/10&123/1250
\end{pmatrix},
\]

its norm is \(126/625+3\sqrt2/10\), and the conjectured bound is
\(324/625\).

## Minimal Dimension

The scalar case is true. For nonnegative scalars \(a,b,c,d\), the left side
is \(4abcd\), while AM-GM gives

\[
\frac{(a+b+c+d)^4}{64}\geq 4abcd.
\]

Consequently, dimension two is the first dimension in which this
counterexample can occur.

## Relation to the Recht-Re Conjecture

Zhang proposed Conjecture 4.1 as a sufficient termwise estimate for a
decomposition intended to imply the full \(m=n=4\) Recht-Re inequality.
The counterexample invalidates that proposed estimate and therefore that
proof route. It does **not** refute the full four-matrix Recht-Re inequality.
Lai and Lim later reported that the full \((m,n)=(4,4)\) case passes their
noncommutative-Positivstellensatz/SDP check.

## Reproduce

From the repository root:

```bash
python research_notes/zhang_conjecture_4_1/run_verification.py
python research_notes/zhang_conjecture_4_1/run_verification.py \
  --output research_notes/zhang_conjecture_4_1/exact_certificate.json
```

The verifier uses SymPy exact rationals and radicals. Floating-point values
are used only to report the positive endpoint \(\rho\).

## Scope

- This resolves the stated inequality by counterexample.
- It does not prove a replacement noncommutative AM-GM inequality.
- It does not establish publication priority.
- It is independent of the Four Color experiments elsewhere in this
  repository.

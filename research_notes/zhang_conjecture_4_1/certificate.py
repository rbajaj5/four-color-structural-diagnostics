"""Exact SymPy certificate for Zhang's four-matrix norm conjecture.

This module uses exact rational and radical arithmetic throughout. It does
not rely on floating-point eigensolvers or numerical optimization.
"""

from __future__ import annotations

from typing import Any

import sympy as sp


def _matrices() -> tuple[sp.Matrix, sp.Matrix, sp.Matrix, sp.Matrix]:
    half = sp.Rational(1, 2)
    a = sp.Matrix([[1, 0], [0, 0]])
    b = sp.Matrix([[0, 0], [0, 1]])
    c = half * sp.Matrix([[1, -1], [-1, 1]])
    d = half * sp.Matrix([[1, 1], [1, 1]])
    return a, b, c, d


def _matrix_strings(matrix: sp.Matrix) -> list[list[str]]:
    return [[str(sp.simplify(value)) for value in row] for row in matrix.tolist()]


def _ordered_eigenvalues(matrix: sp.Matrix) -> list[sp.Expr]:
    eigenvalues = list(matrix.eigenvals())
    return sorted(eigenvalues, key=lambda value: float(sp.N(value, 30)))


def conjecture_expression(
    a: sp.Matrix,
    b: sp.Matrix,
    c: sp.Matrix,
    d: sp.Matrix,
) -> sp.Matrix:
    anticommutator = b * c + c * b
    return sp.simplify(a * anticommutator * d + d * anticommutator * a)


def base_counterexample() -> dict[str, Any]:
    a, b, c, d = _matrices()
    identity = sp.eye(2)

    for matrix in (a, b, c, d):
        assert matrix == matrix.T
        assert matrix * matrix == matrix
        assert set(matrix.eigenvals()).issubset({sp.Integer(0), sp.Integer(1)})

    total = a + b + c + d
    expression = conjecture_expression(a, b, c, d)
    eigenvalues = _ordered_eigenvalues(expression)
    expected_eigenvalues = [
        (-1 - sp.sqrt(2)) / 4,
        (-1 + sp.sqrt(2)) / 4,
    ]
    assert total == 2 * identity
    assert expression == sp.Matrix(
        [[sp.Rational(-1, 2), sp.Rational(-1, 4)], [sp.Rational(-1, 4), 0]]
    )
    assert all(
        sp.simplify(actual - expected) == 0
        for actual, expected in zip(eigenvalues, expected_eigenvalues, strict=True)
    )

    operator_norm = (1 + sp.sqrt(2)) / 4
    conjectured_bound = sp.Rational(1, 64) * 2**4
    violation_gap = sp.simplify(operator_norm - conjectured_bound)
    violation_ratio = sp.simplify(operator_norm / conjectured_bound)
    assert violation_gap.is_positive
    assert violation_ratio == 1 + sp.sqrt(2)

    return {
        "dimension": 2,
        "matrices": {
            "A": _matrix_strings(a),
            "B": _matrix_strings(b),
            "C": _matrix_strings(c),
            "D": _matrix_strings(d),
        },
        "sum": _matrix_strings(total),
        "expression": _matrix_strings(expression),
        "eigenvalues": [str(value) for value in expected_eigenvalues],
        "operator_norm": str(operator_norm),
        "conjectured_bound": str(conjectured_bound),
        "violation_gap": str(violation_gap),
        "violation_ratio": str(violation_ratio),
    }


def positive_definite_counterexample() -> dict[str, Any]:
    t = sp.Rational(1, 10)
    identity = sp.eye(2)
    perturbed = tuple(matrix + t * identity for matrix in _matrices())
    for matrix in perturbed:
        assert all(value.is_positive for value in matrix.eigenvals())

    total = sum(perturbed, sp.zeros(2))
    expression = conjecture_expression(*perturbed)
    expected_expression = sp.Matrix(
        [
            [sp.Rational(-627, 1250), sp.Rational(-3, 10)],
            [sp.Rational(-3, 10), sp.Rational(123, 1250)],
        ]
    )
    expected_eigenvalues = [
        sp.Rational(-126, 625) - 3 * sp.sqrt(2) / 10,
        sp.Rational(-126, 625) + 3 * sp.sqrt(2) / 10,
    ]
    eigenvalues = _ordered_eigenvalues(expression)
    assert total == sp.Rational(12, 5) * identity
    assert expression == expected_expression
    assert all(
        sp.simplify(actual - expected) == 0
        for actual, expected in zip(eigenvalues, expected_eigenvalues, strict=True)
    )

    operator_norm = sp.Rational(126, 625) + 3 * sp.sqrt(2) / 10
    conjectured_bound = sp.Rational(1, 64) * sp.Rational(12, 5) ** 4
    violation_gap = sp.simplify(operator_norm - conjectured_bound)
    assert conjectured_bound == sp.Rational(324, 625)
    assert violation_gap.is_positive

    return {
        "t": str(t),
        "positive_definite": True,
        "smallest_matrix_eigenvalue": str(t),
        "sum": _matrix_strings(total),
        "expression": _matrix_strings(expression),
        "eigenvalues": [str(value) for value in expected_eigenvalues],
        "operator_norm": str(operator_norm),
        "conjectured_bound": str(conjectured_bound),
        "violation_gap": str(violation_gap),
    }


def parametric_family() -> dict[str, Any]:
    t = sp.symbols("t", nonnegative=True, real=True)
    identity = sp.eye(2)
    perturbed = tuple(matrix + t * identity for matrix in _matrices())
    total = sp.simplify(sum(perturbed, sp.zeros(2)))
    expression = sp.simplify(conjecture_expression(*perturbed))
    expected_expression = sp.Matrix(
        [
            [
                4 * t**4 + 8 * t**3 + 4 * t**2 - t / 2 - sp.Rational(1, 2),
                -t / 2 - sp.Rational(1, 4),
            ],
            [
                -t / 2 - sp.Rational(1, 4),
                t * (8 * t**3 + 16 * t**2 + 8 * t + 1) / 2,
            ],
        ]
    )
    assert sp.simplify(expression - expected_expression) == sp.zeros(2)
    assert total == 2 * (1 + 2 * t) * identity

    center = 8 * t**3 + 12 * t**2 + 2 * t - 1
    expected_eigenvalues = [
        (2 * t + 1) * (center - sp.sqrt(2)) / 4,
        (2 * t + 1) * (center + sp.sqrt(2)) / 4,
    ]
    characteristic_polynomial = sp.factor(expression.charpoly().as_expr())
    for eigenvalue in expected_eigenvalues:
        assert sp.simplify(characteristic_polynomial.subs({"lambda": eigenvalue})) == 0

    conjectured_bound = (2 * t + 1) ** 4 / 4
    operator_norm_on_interval = (
        (2 * t + 1)
        * (1 + sp.sqrt(2) - 8 * t**3 - 12 * t**2 - 2 * t)
        / 4
    )
    violation_gap = sp.factor(operator_norm_on_interval - conjectured_bound)
    expected_gap = (
        (2 * t + 1) * (sp.sqrt(2) - 16 * t**3 - 24 * t**2 - 8 * t) / 4
    )
    assert sp.simplify(violation_gap - expected_gap) == 0

    root_polynomial = 16 * t**3 + 24 * t**2 + 8 * t - sp.sqrt(2)
    positive_root = next(
        root
        for root in sp.nroots(root_polynomial, n=40, maxsteps=200)
        if abs(float(sp.im(root))) < 1e-30 and float(sp.re(root)) > 0
    )

    return {
        "parameter_domain": "t >= 0",
        "matrix_family": "A_t=A+tI, B_t=B+tI, C_t=C+tI, D_t=D+tI",
        "sum": "2*(2*t + 1)*I_2",
        "expression": _matrix_strings(expression),
        "eigenvalues": [str(value) for value in expected_eigenvalues],
        "conjectured_bound": str(conjectured_bound),
        "operator_norm_on_violation_interval": str(operator_norm_on_interval),
        "violation_gap": str(expected_gap),
        "violation_interval": "0 <= t < rho",
        "rho_definition": "unique positive root of 16*t^3+24*t^2+8*t=sqrt(2)",
        "rho_numeric": str(positive_root),
    }


def verify_certificate() -> None:
    base_counterexample()
    positive_definite_counterexample()
    parametric_family()


def build_certificate() -> dict[str, Any]:
    verify_certificate()
    return {
        "claim": "Exact counterexample to Zhang (2018), Conjecture 4.1",
        "claim_status": "mathematically verified; literature priority not certified",
        "source": "https://arxiv.org/abs/1411.5058",
        "method": "exact symbolic arithmetic over Q(sqrt(2))",
        "scalar_case": {
            "status": "true",
            "proof": (
                "For nonnegative scalars, the left side is 4abcd and "
                "(a+b+c+d)^4/64 >= 4abcd by AM-GM."
            ),
        },
        "base_counterexample": base_counterexample(),
        "positive_definite_counterexample": positive_definite_counterexample(),
        "parametric_positive_definite_family": parametric_family(),
    }

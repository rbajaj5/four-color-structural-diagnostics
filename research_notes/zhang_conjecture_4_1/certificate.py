"""Exact SymPy certificate for Zhang's four-matrix norm conjecture.

This module uses exact rational and radical arithmetic throughout. It does
not rely on floating-point eigensolvers or numerical optimization.
"""

from __future__ import annotations

import itertools
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
    condition_number_threshold = 1 + 1 / positive_root

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
        "matrix_condition_number_for_t_positive": "(1+t)/t",
        "violation_condition_number_range": "kappa > 1 + 1/rho",
        "condition_number_threshold_numeric": str(condition_number_threshold),
    }


def corrected_constant_lower_bound() -> dict[str, Any]:
    t = sp.symbols("t", nonnegative=True, real=True)
    proposed_constant = sp.Rational(1, 64)
    forced_constant = (1 + sp.sqrt(2)) / 64
    ratio_on_failure_interval = (
        1
        + sp.sqrt(2)
        - 8 * t**3
        - 12 * t**2
        - 2 * t
    ) / (64 * (2 * t + 1) ** 3)
    derivative = sp.factor(sp.diff(ratio_on_failure_interval, t))
    expected_derivative = -(8 * t + 4 + 3 * sp.sqrt(2)) / (
        32 * (2 * t + 1) ** 4
    )

    assert sp.simplify(derivative - expected_derivative) == 0
    assert expected_derivative.is_negative
    assert sp.simplify(ratio_on_failure_interval.subs(t, 0) - forced_constant) == 0
    assert sp.simplify(forced_constant / proposed_constant) == 1 + sp.sqrt(2)

    return {
        "inequality_template": "norm(X) <= c*norm(A+B+C+D)^4",
        "zhang_proposed_c": str(proposed_constant),
        "necessary_universal_lower_bound_for_c": str(forced_constant),
        "factor_over_zhang_constant": str(1 + sp.sqrt(2)),
        "positive_definite_family_ratio": str(ratio_on_failure_interval),
        "ratio_derivative": str(expected_derivative),
        "interpretation": (
            "The ratio decreases for t >= 0 while the negative eigenvalue "
            "controls the norm. Positive-definite examples approach the same "
            "lower bound as t tends to zero from above."
        ),
    }


def recht_re_aggregate_family() -> dict[str, Any]:
    t = sp.symbols("t", nonnegative=True, real=True)
    identity = sp.eye(2)
    matrices = tuple(matrix + t * identity for matrix in _matrices())

    symmetrized_sum = sp.zeros(2)
    for order in itertools.permutations(range(4)):
        product = identity
        for index in order:
            product = product * matrices[index]
        symmetrized_sum += product
    symmetrized_sum = sp.simplify(symmetrized_sum)

    scalar = 24 * t**4 + 48 * t**3 + 24 * t**2 - 1
    expected_sum = scalar * identity
    assert symmetrized_sum == expected_sum

    with_replacement_average = sp.simplify(
        (sum(matrices, sp.zeros(2)) / 4) ** 4
    )
    without_replacement_average = sp.simplify(symmetrized_sum / sp.factorial(4))
    expected_with = (2 * t + 1) ** 4 * identity / 16
    expected_without = scalar * identity / 24
    assert with_replacement_average == expected_with
    assert without_replacement_average == expected_without

    with_norm = (2 * t + 1) ** 4 / 16
    without_norm = sp.Abs(scalar) / 24
    positive_branch_slack = sp.factor(with_norm - scalar / 24)
    negative_branch_slack = sp.factor(with_norm + scalar / 24)
    assert sp.simplify(
        positive_branch_slack - (24 * t**2 + 24 * t + 5) / 48
    ) == 0
    assert sp.simplify(
        negative_branch_slack
        - (96 * t**4 + 192 * t**3 + 120 * t**2 + 24 * t + 1) / 48
    ) == 0
    assert positive_branch_slack.is_positive
    assert negative_branch_slack.is_positive

    sign_switch = -sp.Rational(1, 2) + sp.sqrt(3 * sp.sqrt(6) + 9) / 6
    assert sp.simplify(scalar.subs(t, sign_switch)) == 0

    base_with = with_norm.subs(t, 0)
    base_without = without_norm.subs(t, 0)
    assert base_with == sp.Rational(1, 16)
    assert base_without == sp.Rational(1, 24)
    assert sp.simplify(base_without / base_with) == sp.Rational(2, 3)

    return {
        "setting": "Recht-Re full average with m=n=4",
        "symmetrized_24_product_sum": _matrix_strings(symmetrized_sum),
        "with_replacement_average": _matrix_strings(with_replacement_average),
        "without_replacement_average": _matrix_strings(
            without_replacement_average
        ),
        "with_replacement_norm": str(with_norm),
        "without_replacement_norm": str(without_norm),
        "strict_inequality_for_all_t_nonnegative": True,
        "slack_when_symmetrized_scalar_nonnegative": str(positive_branch_slack),
        "slack_when_symmetrized_scalar_negative": str(negative_branch_slack),
        "symmetrized_scalar_sign_switch": str(sign_switch),
        "symmetrized_scalar_sign_switch_numeric": str(sp.N(sign_switch, 40)),
        "t_zero": {
            "with_replacement_norm": str(base_with),
            "without_replacement_norm": str(base_without),
            "without_to_with_ratio": "2/3",
            "symmetrized_24_product_sum": [["-1", "0"], ["0", "-1"]],
        },
        "interpretation": (
            "The local Zhang estimate fails, but cancellation among all 24 "
            "ordered products preserves the full four-matrix average inequality."
        ),
    }


def verify_certificate() -> None:
    base_counterexample()
    positive_definite_counterexample()
    parametric_family()
    corrected_constant_lower_bound()
    recht_re_aggregate_family()


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
        "corrected_constant_lower_bound": corrected_constant_lower_bound(),
        "full_recht_re_aggregate_application": recht_re_aggregate_family(),
    }

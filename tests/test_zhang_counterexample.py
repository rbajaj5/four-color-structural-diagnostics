import sympy as sp

from research_notes.zhang_conjecture_4_1.certificate import (
    base_counterexample,
    build_certificate,
    parametric_family,
    positive_definite_counterexample,
)


def test_rank_one_projector_counterexample_is_exact() -> None:
    result = base_counterexample()
    assert result["operator_norm"] == "1/4 + sqrt(2)/4"
    assert result["conjectured_bound"] == "1/4"
    assert result["violation_ratio"] == "1 + sqrt(2)"


def test_positive_definite_counterexample_is_exact() -> None:
    result = positive_definite_counterexample()
    assert result["positive_definite"] is True
    assert result["t"] == "1/10"
    assert result["conjectured_bound"] == "324/625"
    assert sp.sympify(result["violation_gap"]).is_positive


def test_parametric_failure_interval_contains_one_tenth() -> None:
    result = parametric_family()
    rho = float(result["rho_numeric"])
    assert rho > 0.1
    assert rho < 0.126


def test_full_certificate_records_priority_caution() -> None:
    result = build_certificate()
    assert result["claim_status"] == (
        "mathematically verified; literature priority not certified"
    )

import sympy as sp

from research_notes.zhang_conjecture_4_1.certificate import (
    base_counterexample,
    build_certificate,
    corrected_constant_lower_bound,
    parametric_family,
    positive_definite_counterexample,
    recht_re_aggregate_family,
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
    assert 8.96 < float(result["condition_number_threshold_numeric"]) < 8.97


def test_full_certificate_records_priority_caution() -> None:
    result = build_certificate()
    assert result["claim_status"] == (
        "mathematically verified; literature priority not certified"
    )


def test_counterexample_forces_larger_termwise_constant() -> None:
    result = corrected_constant_lower_bound()
    assert result["zhang_proposed_c"] == "1/64"
    assert result["necessary_universal_lower_bound_for_c"] == (
        "1/64 + sqrt(2)/64"
    )
    assert result["factor_over_zhang_constant"] == "1 + sqrt(2)"


def test_full_recht_re_average_survives_by_cancellation() -> None:
    result = recht_re_aggregate_family()
    assert result["strict_inequality_for_all_t_nonnegative"] is True
    assert result["t_zero"]["with_replacement_norm"] == "1/16"
    assert result["t_zero"]["without_replacement_norm"] == "1/24"
    assert result["t_zero"]["without_to_with_ratio"] == "2/3"

from __future__ import annotations

import math

import pytest

from genai_at_work.cps_uncertainty import (
    GVFBorrowingParameters,
    UncertaintySupport,
    approximate_composition_marginal_standard_errors,
    approximate_percentage_standard_error,
    build_composition_covariance,
    composition_counterfactual_standard_error,
    composition_covariance_from_level_covariance,
    pooled_composition_covariance_from_month_block,
)


def _gvf_parameters() -> GVFBorrowingParameters:
    return GVFBorrowingParameters(
        alpha=-4841.52,
        beta=0.00003413,
        factor=1.0,
        lender_series="BLS PF-9 part-time workers example",
        borrowing_rationale="test fixture reproducing the published percentage example",
    )


def test_bls_percentage_gvf_formula_reproduces_published_example() -> None:
    standard_error = approximate_percentage_standard_error(
        17.3,
        156_000_000,
        _gvf_parameters(),
    )
    assert math.isclose(standard_error, 0.06653944076202528, rel_tol=1e-12)


def test_gvf_composition_result_is_explicitly_marginal_only() -> None:
    parameters = {"a": _gvf_parameters(), "b": _gvf_parameters()}
    result = approximate_composition_marginal_standard_errors(
        {"a": 0.4, "b": 0.6},
        denominator=156_000_000,
        parameters=parameters,
    )
    assert result.support is UncertaintySupport.GVF_MARGINAL_APPROXIMATION
    assert result.covariance_available is False
    assert result.occupation_ids == ("a", "b")
    assert all(value >= 0.0 for value in result.standard_errors)


def test_gvf_negative_variance_fails_closed() -> None:
    unsupported = GVFBorrowingParameters(
        alpha=-10_000.0,
        beta=0.0,
        factor=1.0,
        lender_series="unsupported fixture",
        borrowing_rationale="exercise negative-radicand guard",
    )
    with pytest.raises(ValueError, match="negative variance"):
        approximate_percentage_standard_error(50.0, 100.0, unsupported)


def test_marginal_variances_are_rejected_as_composition_covariance() -> None:
    with pytest.raises(ValueError, match="sum-to-one constraint"):
        build_composition_covariance(
            ("a", "b"),
            (0.4, 0.6),
            ((0.01, 0.0), (0.0, 0.01)),
            source_method="invalid independent marginal approximation",
        )


def test_delta_method_composition_covariance_respects_simplex() -> None:
    result = composition_covariance_from_level_covariance(
        ("a", "b"),
        (60.0, 40.0),
        ((25.0, 0.0), (0.0, 16.0)),
        source_method="synthetic full level covariance",
    )
    assert result.support is UncertaintySupport.DESIGN_COVARIANCE
    assert result.shares == (0.6, 0.4)
    assert math.isclose(sum(result.covariance[0]), 0.0, abs_tol=1e-12)
    assert math.isclose(sum(result.covariance[1]), 0.0, abs_tol=1e-12)
    assert math.isclose(result.covariance[0][0], result.covariance[1][1], abs_tol=1e-12)
    assert math.isclose(result.covariance[0][1], -result.covariance[0][0], abs_tol=1e-12)


def test_constant_occupation_outcome_has_zero_composition_uncertainty() -> None:
    result = composition_covariance_from_level_covariance(
        ("a", "b"),
        (60.0, 40.0),
        ((25.0, 0.0), (0.0, 16.0)),
        source_method="synthetic full level covariance",
    )
    standard_error = composition_counterfactual_standard_error(
        result,
        {"a": 0.25, "b": 0.25},
    )
    assert math.isclose(standard_error, 0.0, abs_tol=1e-12)


def test_nonconstant_counterfactual_propagates_covariance() -> None:
    result = composition_covariance_from_level_covariance(
        ("a", "b"),
        (60.0, 40.0),
        ((25.0, 0.0), (0.0, 16.0)),
        source_method="synthetic full level covariance",
    )
    standard_error = composition_counterfactual_standard_error(
        result,
        {"a": 0.1, "b": 0.7},
    )
    assert standard_error > 0.0


def test_pooled_month_covariance_uses_cross_month_blocks() -> None:
    # Two months, two occupations. The off-diagonal month blocks are nonzero to ensure the
    # pooling transformation actually carries cross-month dependence into the quarter estimate.
    block = (
        (4.0, 0.0, 1.0, 0.0),
        (0.0, 4.0, 0.0, 1.0),
        (1.0, 0.0, 4.0, 0.0),
        (0.0, 1.0, 0.0, 4.0),
    )
    result = pooled_composition_covariance_from_month_block(
        ("a", "b"),
        ((60.0, 40.0), (62.0, 38.0)),
        block,
        source_method="synthetic full cross-month covariance",
    )
    assert math.isclose(sum(result.shares), 1.0, abs_tol=1e-12)
    assert result.covariance[0][0] > 0.0
    assert math.isclose(sum(result.covariance[0]), 0.0, abs_tol=1e-12)


def test_pooled_month_covariance_requires_full_block_dimension() -> None:
    with pytest.raises(ValueError, match="covariance dimension"):
        pooled_composition_covariance_from_month_block(
            ("a", "b"),
            ((60.0, 40.0), (62.0, 38.0)),
            ((1.0, 0.0), (0.0, 1.0)),
            source_method="incomplete covariance fixture",
        )

from __future__ import annotations

import pytest

from genai_at_work.metrics.conversion import (
    composition_counterfactual,
    feasible_composition_interval,
    fit_ols,
    residuals,
)


def test_fit_ols_exact_line() -> None:
    fit = fit_ols([1.0, 2.0, 3.0], [3.0, 5.0, 7.0])
    assert fit.intercept == pytest.approx(1.0)
    assert fit.slope == pytest.approx(2.0)


def test_residuals_sum_to_zero_with_intercept() -> None:
    values = residuals([1.0, 2.0, 4.0, 7.0], [2.0, 2.5, 5.0, 6.0])
    assert sum(values) == pytest.approx(0.0, abs=1e-12)


def test_composition_counterfactual_forbids_silent_renormalization() -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        composition_counterfactual([0.4, 0.5], [10.0, 20.0])


def test_composition_counterfactual() -> None:
    assert composition_counterfactual([0.25, 0.75], [20.0, 60.0]) == pytest.approx(50.0)


def test_feasible_interval() -> None:
    lower, upper = feasible_composition_interval(
        [0.25, 0.75], [10.0, 20.0], [30.0, 60.0]
    )
    assert lower == pytest.approx(17.5)
    assert upper == pytest.approx(52.5)

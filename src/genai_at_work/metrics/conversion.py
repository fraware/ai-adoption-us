"""Descriptive conversion metrics used by the publication.

Nothing in this module has a causal interpretation. Functions are intentionally small and
explicit so that the website can expose their exact formulas.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LinearFit:
    intercept: float
    slope: float

    def predict(self, x: float) -> float:
        return self.intercept + self.slope * x


def fit_ols(x: list[float], y: list[float]) -> LinearFit:
    """Fit a one-predictor OLS line using population-moment algebra.

    Raises on mismatched lengths, fewer than two points, or zero predictor variance.
    This function is used only for descriptive quarter-specific residual views.
    """

    if len(x) != len(y):
        raise ValueError("x and y must have identical lengths")
    if len(x) < 2:
        raise ValueError("at least two observations are required")

    x_bar = sum(x) / len(x)
    y_bar = sum(y) / len(y)
    ss_x = sum((value - x_bar) ** 2 for value in x)
    if ss_x == 0:
        raise ValueError("x has zero variance")
    covariance = sum((xi - x_bar) * (yi - y_bar) for xi, yi in zip(x, y, strict=True))
    slope = covariance / ss_x
    return LinearFit(intercept=y_bar - slope * x_bar, slope=slope)


def residuals(x: list[float], y: list[float]) -> list[float]:
    """Return `y - E_hat[y|x]` from a descriptive one-predictor OLS fit."""

    fit = fit_ols(x, y)
    return [yi - fit.predict(xi) for xi, yi in zip(x, y, strict=True)]


def composition_counterfactual(shares: list[float], outcomes: list[float]) -> float:
    """Compute a weighted composition counterfactual after validating shares.

    Both arrays must refer to the same exhaustive set of categories. The shares must sum to
    one within numerical tolerance. Missing categories must be resolved before this function
    is called; silent renormalization is intentionally forbidden.
    """

    if len(shares) != len(outcomes):
        raise ValueError("shares and outcomes must have identical lengths")
    if not shares:
        raise ValueError("at least one category is required")
    if any(share < 0 for share in shares):
        raise ValueError("composition shares cannot be negative")
    total = sum(shares)
    if abs(total - 1.0) > 1e-8:
        raise ValueError(f"composition shares must sum to 1; got {total}")
    return sum(share * outcome for share, outcome in zip(shares, outcomes, strict=True))


def feasible_composition_interval(
    broad_shares: list[float], within_group_min: list[float], within_group_max: list[float]
) -> tuple[float, float]:
    """Return a partial-identification interval under coarse category shares.

    For each broad category, all unknown within-category mass is allowed to concentrate on
    the minimum- or maximum-outcome compatible detailed category.
    """

    if not (len(broad_shares) == len(within_group_min) == len(within_group_max)):
        raise ValueError("all inputs must have identical lengths")
    if abs(sum(broad_shares) - 1.0) > 1e-8:
        raise ValueError("broad shares must sum to 1")
    if any(lo > hi for lo, hi in zip(within_group_min, within_group_max, strict=True)):
        raise ValueError("each minimum must be <= its maximum")

    lower = sum(w * lo for w, lo in zip(broad_shares, within_group_min, strict=True))
    upper = sum(w * hi for w, hi in zip(broad_shares, within_group_max, strict=True))
    return lower, upper

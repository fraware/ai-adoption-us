"""Uncertainty primitives for custom CPS occupation-composition vectors.

The observatory keeps inferential uncertainty separate from descriptive reliability diagnostics.
This module supports two deliberately different computational evidence classes:

* covariance-aware composition uncertainty, when a full covariance for the underlying CPS
  weighted levels (or composition shares) is supplied; and
* BLS-style generalized-variance-function (GVF) marginal standard-error approximations,
  which are useful for benchmarking but do not identify the covariance matrix of a composition.

A covariance-aware result is a mathematical capability, not an automatic claim of CPS
survey-design validity. Whether an input covariance is design-based must be established by its
provenance and the release gate. No function in this module interprets Kish weight dispersion,
month-to-month perturbations, or leave-one-month-out diagnostics as design-based uncertainty.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar


class UncertaintySupport(StrEnum):
    """Computational support class for an uncertainty result."""

    COVARIANCE_AWARE = "covariance_aware"
    GVF_MARGINAL_APPROXIMATION = "gvf_marginal_approximation"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class GVFBorrowingParameters:
    """Parameters used in the BLS approximate percentage standard-error formula.

    ``factor`` is the BLS period/change factor associated with the lending series. For a
    single-month estimate it is normally 1.0. Borrowing these parameters is an approximation:
    BLS states that it assumes approximately equal design effects between the lending and
    borrowing series.
    """

    alpha: float
    beta: float
    factor: float
    lender_series: str
    borrowing_rationale: str


@dataclass(frozen=True)
class GVFMarginalCompositionUncertainty:
    """Marginal share standard errors without a composition covariance matrix."""

    occupation_ids: tuple[str, ...]
    shares: tuple[float, ...]
    standard_errors: tuple[float, ...]
    support: ClassVar[UncertaintySupport] = UncertaintySupport.GVF_MARGINAL_APPROXIMATION
    covariance_available: ClassVar[bool] = False


@dataclass(frozen=True)
class CompositionCovariance:
    """Structurally validated covariance matrix for a probability/composition vector.

    Instances returned by :func:`build_composition_covariance` satisfy the numerical covariance
    and simplex constraints enforced by this module. ``support`` deliberately says only that a
    full covariance is available. It does not certify the survey-design provenance of that matrix.
    """

    occupation_ids: tuple[str, ...]
    shares: tuple[float, ...]
    covariance: tuple[tuple[float, ...], ...]
    source_method: str
    support: ClassVar[UncertaintySupport] = UncertaintySupport.COVARIANCE_AWARE


def _require_finite(value: float, *, field: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{field} must be finite")
    return value


def _validate_labels_and_values(
    occupation_ids: Sequence[str],
    values: Sequence[float],
    *,
    field: str,
) -> tuple[tuple[str, ...], tuple[float, ...]]:
    labels = tuple(str(label) for label in occupation_ids)
    numeric = tuple(_require_finite(value, field=field) for value in values)
    if not labels:
        raise ValueError("occupation_ids must not be empty")
    if len(labels) != len(numeric):
        raise ValueError(f"occupation_ids and {field} must have the same length")
    if len(set(labels)) != len(labels):
        raise ValueError("occupation_ids must be unique")
    return labels, numeric


def _validate_square_covariance(
    covariance: Sequence[Sequence[float]],
    *,
    dimension: int,
    tolerance: float,
    require_simplex_constraint: bool,
) -> tuple[tuple[float, ...], ...]:
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")
    if len(covariance) != dimension:
        raise ValueError("covariance dimension does not match estimate vector")

    matrix: list[tuple[float, ...]] = []
    for row in covariance:
        if len(row) != dimension:
            raise ValueError("covariance matrix must be square")
        matrix.append(tuple(_require_finite(value, field="covariance") for value in row))

    for i in range(dimension):
        if matrix[i][i] < -tolerance:
            raise ValueError("covariance diagonal contains a negative variance")
        for j in range(i + 1, dimension):
            scale = max(1.0, abs(matrix[i][j]), abs(matrix[j][i]))
            if abs(matrix[i][j] - matrix[j][i]) > tolerance * scale:
                raise ValueError("covariance matrix must be symmetric")

    # Cholesky-style positive-semidefinite check that permits zero pivots. Composition
    # covariance matrices are necessarily singular because their rows/columns sum to zero.
    lower = [[0.0 for _ in range(dimension)] for _ in range(dimension)]
    for i in range(dimension):
        diagonal = matrix[i][i] - sum(lower[i][k] ** 2 for k in range(i))
        scale = max(1.0, abs(matrix[i][i]))
        if diagonal < -tolerance * scale:
            raise ValueError("covariance matrix is not positive semidefinite")
        if diagonal <= tolerance * scale:
            lower[i][i] = 0.0
            for j in range(i + 1, dimension):
                residual = matrix[j][i] - sum(lower[j][k] * lower[i][k] for k in range(i))
                residual_scale = max(1.0, abs(matrix[j][i]))
                if abs(residual) > tolerance * residual_scale:
                    raise ValueError("covariance matrix is not positive semidefinite")
        else:
            lower[i][i] = math.sqrt(diagonal)
            for j in range(i + 1, dimension):
                residual = matrix[j][i] - sum(lower[j][k] * lower[i][k] for k in range(i))
                lower[j][i] = residual / lower[i][i]

    if require_simplex_constraint:
        matrix_scale = max(1.0, max(abs(value) for row in matrix for value in row))
        for row in matrix:
            if abs(sum(row)) > tolerance * matrix_scale * dimension:
                raise ValueError(
                    "composition covariance must respect the sum-to-one constraint; "
                    "marginal variances alone are insufficient"
                )

    return tuple(matrix)


def approximate_percentage_standard_error(
    percent: float,
    denominator: float,
    parameters: GVFBorrowingParameters,
) -> float:
    """Return the BLS-style approximate standard error of a percentage.

    The implemented formula is::

        se(p; y; f) = f * sqrt(((alpha + beta*y) / y) * p * (100 - p))

    where ``p`` is in percentage points and ``y`` is the full-precision denominator level.
    The result is also in percentage points. This function implements the published arithmetic;
    it does not establish that the supplied lending series is a defensible design-effect match.
    """

    p = _require_finite(percent, field="percent")
    y = _require_finite(denominator, field="denominator")
    alpha = _require_finite(parameters.alpha, field="alpha")
    beta = _require_finite(parameters.beta, field="beta")
    factor = _require_finite(parameters.factor, field="factor")
    if not 0.0 <= p <= 100.0:
        raise ValueError("percent must lie in [0, 100]")
    if y <= 0.0:
        raise ValueError("denominator must be positive")
    if factor <= 0.0:
        raise ValueError("factor must be positive")
    if not parameters.lender_series.strip():
        raise ValueError("lender_series must be recorded")
    if not parameters.borrowing_rationale.strip():
        raise ValueError("borrowing_rationale must be recorded")

    radicand = ((alpha + beta * y) / y) * p * (100.0 - p)
    if radicand < -1e-15:
        raise ValueError(
            "GVF parameters produce a negative variance for this estimate; "
            "the borrowing specification is unsupported"
        )
    return factor * math.sqrt(max(0.0, radicand))


def approximate_composition_marginal_standard_errors(
    shares: Mapping[str, float],
    *,
    denominator: float,
    parameters: Mapping[str, GVFBorrowingParameters],
) -> GVFMarginalCompositionUncertainty:
    """Compute GVF marginal SEs for composition shares, explicitly without covariance.

    Returned standard errors are in share units (0--1). The result must not be used as though
    the shares were independent: a composition sums to one, so its covariance structure is
    essential for joint inference and for propagating uncertainty to weighted counterfactuals.
    """

    labels = tuple(sorted(shares))
    if not labels:
        raise ValueError("shares must not be empty")
    if set(labels) != set(parameters):
        raise ValueError("GVF parameters must be supplied for exactly the composition occupations")
    vector = tuple(_require_finite(shares[label], field="share") for label in labels)
    if any(value < 0.0 or value > 1.0 for value in vector):
        raise ValueError("composition shares must lie in [0, 1]")
    if not math.isclose(sum(vector), 1.0, rel_tol=0.0, abs_tol=1e-10):
        raise ValueError("composition shares must sum to one")

    standard_errors = tuple(
        approximate_percentage_standard_error(
            100.0 * share,
            denominator,
            parameters[label],
        )
        / 100.0
        for label, share in zip(labels, vector, strict=True)
    )
    return GVFMarginalCompositionUncertainty(
        occupation_ids=labels,
        shares=vector,
        standard_errors=standard_errors,
    )


def build_composition_covariance(
    occupation_ids: Sequence[str],
    shares: Sequence[float],
    covariance: Sequence[Sequence[float]],
    *,
    source_method: str,
    tolerance: float = 1e-10,
) -> CompositionCovariance:
    """Validate and construct a covariance-aware composition uncertainty object.

    Structural validation does not establish survey-design validity. ``source_method`` must record
    the covariance provenance so an upstream methodological/release gate can decide whether a
    design-based claim is warranted.
    """

    labels, vector = _validate_labels_and_values(occupation_ids, shares, field="shares")
    if any(value < -tolerance or value > 1.0 + tolerance for value in vector):
        raise ValueError("composition shares must lie in [0, 1]")
    if not math.isclose(sum(vector), 1.0, rel_tol=0.0, abs_tol=tolerance * len(vector)):
        raise ValueError("composition shares must sum to one")
    if not source_method.strip():
        raise ValueError("source_method must identify the covariance provenance")
    matrix = _validate_square_covariance(
        covariance,
        dimension=len(vector),
        tolerance=tolerance,
        require_simplex_constraint=True,
    )
    return CompositionCovariance(
        occupation_ids=labels,
        shares=vector,
        covariance=matrix,
        source_method=source_method,
    )


def composition_covariance_from_level_covariance(
    occupation_ids: Sequence[str],
    levels: Sequence[float],
    level_covariance: Sequence[Sequence[float]],
    *,
    source_method: str,
    tolerance: float = 1e-10,
) -> CompositionCovariance:
    """Propagate a full covariance of occupation levels to occupation shares by delta method.

    Let ``w_i = x_i / sum(x)``. The Jacobian is
    ``J[i,k] = (1{i=k} - w_i) / sum(x)``. The returned covariance is ``J C J'``.

    This transformation is only as design-valid as ``level_covariance``. Passing independent
    marginal variances, a Kish approximation, or perturbation diagnostics does not make the result
    CPS design-based.
    """

    labels, numeric_levels = _validate_labels_and_values(occupation_ids, levels, field="levels")
    if any(value < 0.0 for value in numeric_levels):
        raise ValueError("occupation levels must be nonnegative")
    total = sum(numeric_levels)
    if total <= 0.0:
        raise ValueError("occupation levels must have a positive total")
    level_matrix = _validate_square_covariance(
        level_covariance,
        dimension=len(numeric_levels),
        tolerance=tolerance,
        require_simplex_constraint=False,
    )
    shares = tuple(value / total for value in numeric_levels)
    dimension = len(shares)
    jacobian = [
        [((1.0 if i == k else 0.0) - shares[i]) / total for k in range(dimension)]
        for i in range(dimension)
    ]
    left_product = [
        [
            sum(jacobian[i][k] * level_matrix[k][j] for k in range(dimension))
            for j in range(dimension)
        ]
        for i in range(dimension)
    ]
    share_covariance = [
        [
            sum(left_product[i][k] * jacobian[j][k] for k in range(dimension))
            for j in range(dimension)
        ]
        for i in range(dimension)
    ]
    return build_composition_covariance(
        labels,
        shares,
        share_covariance,
        source_method=source_method,
        tolerance=tolerance,
    )


def pooled_composition_covariance_from_month_block(
    occupation_ids: Sequence[str],
    monthly_levels: Sequence[Sequence[float]],
    month_block_covariance: Sequence[Sequence[float]],
    *,
    source_method: str,
    tolerance: float = 1e-10,
) -> CompositionCovariance:
    """Pool monthly level estimates using their complete cross-month covariance block.

    ``month_block_covariance`` is ordered month-major: all occupations for month 1, followed by
    all occupations for month 2, and so on. Off-diagonal month blocks are required inputs, not
    inferred as zero. That contract prevents the rotating-panel dependence of CPS months from
    being silently discarded.

    Equal-month averaging of occupation levels is used before converting levels to shares. With
    equal month factors, the resulting shares equal ratios formed from summed monthly levels.
    """

    labels = tuple(str(label) for label in occupation_ids)
    if not labels or len(set(labels)) != len(labels):
        raise ValueError("occupation_ids must be nonempty and unique")
    if len(monthly_levels) < 2:
        raise ValueError("at least two months are required for pooled covariance")
    dimension = len(labels)
    numeric_months: list[tuple[float, ...]] = []
    for values in monthly_levels:
        _, numeric = _validate_labels_and_values(labels, values, field="monthly_levels")
        if any(value < 0.0 for value in numeric):
            raise ValueError("monthly occupation levels must be nonnegative")
        numeric_months.append(numeric)

    block_dimension = len(numeric_months) * dimension
    block = _validate_square_covariance(
        month_block_covariance,
        dimension=block_dimension,
        tolerance=tolerance,
        require_simplex_constraint=False,
    )
    month_count = len(numeric_months)
    pooled_levels = tuple(
        sum(month[occupation] for month in numeric_months) / month_count
        for occupation in range(dimension)
    )
    pooled_level_covariance = [
        [
            sum(
                block[left_month * dimension + i][right_month * dimension + j]
                for left_month in range(month_count)
                for right_month in range(month_count)
            )
            / (month_count**2)
            for j in range(dimension)
        ]
        for i in range(dimension)
    ]
    return composition_covariance_from_level_covariance(
        labels,
        pooled_levels,
        pooled_level_covariance,
        source_method=source_method,
        tolerance=tolerance,
    )


def composition_counterfactual_standard_error(
    composition: CompositionCovariance,
    occupation_values: Mapping[str, float],
) -> float:
    """Propagate composition covariance to a fixed occupation-weighted counterfactual.

    This is the composition-covariance component only: occupation outcome values are treated as
    fixed. Whether ``composition`` is CPS design-based is an upstream provenance question. RPS
    sampling uncertainty, covariance between RPS occupation estimates, and cross-source dependence
    are outside this function and must be handled separately before a total inferential standard
    error is claimed.
    """

    if set(occupation_values) != set(composition.occupation_ids):
        raise ValueError("occupation_values must match the covariance occupation universe exactly")
    values = tuple(
        _require_finite(occupation_values[label], field="occupation value")
        for label in composition.occupation_ids
    )
    variance = sum(
        values[i] * composition.covariance[i][j] * values[j]
        for i in range(len(values))
        for j in range(len(values))
    )
    if variance < -1e-15:
        raise ValueError("propagated variance is negative")
    return math.sqrt(max(0.0, variance))

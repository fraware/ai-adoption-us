"""Evidence and identifiability contracts for CPS design-based composition variance.

The public Basic Monthly CPS files support point estimation but do not, on the official
materials reviewed for this project, expose the internal 160-replicate successive-difference
replication system used to estimate CPS variances and covariances. BLS generalized variance
functions can approximate marginal standard errors for eligible or defensibly borrowed scalar
series, including period/change factors, but those quantities do not identify the covariance
matrix of a multi-part composition.

This module makes that distinction testable. It does not estimate a survey-design covariance.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class CompositionCovarianceIdentifiability:
    """Parameter count for a composition covariance with known marginal variances.

    A symmetric ``k x k`` covariance has ``k(k+1)/2`` unique entries. The composition
    constraint ``C 1 = 0`` imposes ``k`` independent linear constraints, leaving
    ``k(k-1)/2`` free parameters. If all ``k`` marginal variances are additionally fixed,
    ``k(k-3)/2`` off-diagonal degrees of freedom remain for ``k >= 3``.

    The count is an identifiability statement, not a claim that every arbitrary assignment
    of the remaining parameters is positive semidefinite.
    """

    dimension: int
    symmetric_parameter_count: int
    simplex_constraint_count: int
    parameters_after_simplex_constraint: int
    marginal_variance_count: int
    unidentified_parameters_after_marginals: int


def composition_covariance_identifiability(
    dimension: int,
) -> CompositionCovarianceIdentifiability:
    """Return covariance parameter counts for a composition of at least three parts."""

    if dimension < 3:
        raise ValueError("composition covariance identifiability requires dimension >= 3")
    symmetric = dimension * (dimension + 1) // 2
    after_simplex = dimension * (dimension - 1) // 2
    unidentified = dimension * (dimension - 3) // 2
    return CompositionCovarianceIdentifiability(
        dimension=dimension,
        symmetric_parameter_count=symmetric,
        simplex_constraint_count=dimension,
        parameters_after_simplex_constraint=after_simplex,
        marginal_variance_count=dimension,
        unidentified_parameters_after_marginals=unidentified,
    )


def validate_public_design_variance_decision(decision: Mapping[str, object]) -> None:
    """Fail closed unless the registry records the current unsupported public design path.

    This validator deliberately pins the scientific boundary relevant to the observatory's
    22-occupation, three-month pooled composition vectors. A future transition to supported
    design-based covariance must change this contract explicitly and arrive with new evidence,
    tests, and review rather than silently broadening the current state.
    """

    if decision.get("schema_version") != 1:
        raise ValueError("CPS design-variance decision schema_version must equal 1")
    if decision.get("decision_status") != "PUBLIC_FULL_DESIGN_COVARIANCE_UNSUPPORTED":
        raise ValueError("unexpected CPS public design-variance decision status")

    target = decision.get("target")
    if not isinstance(target, dict):
        raise ValueError("CPS design-variance decision lacks target object")
    if target.get("occupation_dimension") != 22 or target.get("quarter_month_count") != 3:
        raise ValueError("CPS design-variance target must remain 22 occupations over 3 months")

    public_path = decision.get("public_variance_path")
    if not isinstance(public_path, dict):
        raise ValueError("CPS design-variance decision lacks public_variance_path")
    if public_path.get("basic_monthly_public_replicate_system_identified") is not False:
        raise ValueError("public replicate-system evidence state must fail closed")
    if public_path.get("gvf_full_composition_covariance_identified") is not False:
        raise ValueError("GVF must not be represented as identifying full composition covariance")
    if public_path.get("gvf_scalar_or_marginal_approximation_available") is not True:
        raise ValueError("decision must preserve the supported scalar/marginal GVF capability")

    identifiability = decision.get("identifiability")
    if not isinstance(identifiability, dict):
        raise ValueError("CPS design-variance decision lacks identifiability object")
    expected = composition_covariance_identifiability(22)
    expected_values = {
        "symmetric_parameter_count": expected.symmetric_parameter_count,
        "simplex_constraint_count": expected.simplex_constraint_count,
        "parameters_after_simplex_constraint": expected.parameters_after_simplex_constraint,
        "marginal_variance_count": expected.marginal_variance_count,
        "unidentified_parameters_after_marginals": expected.unidentified_parameters_after_marginals,
    }
    for field, value in expected_values.items():
        if identifiability.get(field) != value:
            raise ValueError(f"CPS design-variance identifiability mismatch for {field}")

    publication = decision.get("publication")
    if not isinstance(publication, dict):
        raise ValueError("CPS design-variance decision lacks publication object")
    required_false = (
        "design_based_composition_interval_allowed",
        "pooled_quarter_design_based_interval_allowed",
        "occupation_adjusted_rps_residual_interval_allowed",
    )
    for field in required_false:
        if publication.get(field) is not False:
            raise ValueError(f"{field} must remain false until a design-valid covariance path exists")
    if publication.get("gvf_marginal_benchmark_allowed") is not True:
        raise ValueError("GVF marginal benchmarking should remain available with explicit provenance")

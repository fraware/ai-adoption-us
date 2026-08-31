# CPS quarter availability

The composition layer is defined on three calendar Basic Monthly CPS cross-sections aligned to each RPS quarter. Missing months are a change in data availability, not a license to redefine the quarter.

## Q4 2025

October 2025 CPS interviewing was not conducted during the federal government shutdown. The Phase 4 pipeline therefore marks `2025-Q4` as **unavailable** for CPS composition.

It does not:

- substitute another month;
- pool November and December alone;
- impute October;
- rescale the two available months and label the result a Q4 estimate.

Those alternatives target a different object and could create spurious quarter-to-quarter comparisons. The unavailable state is machine-readable in `data/registry/cps_quarter_availability.yaml` and enforced before network fetching.

This does not remove Q4 2025 RPS observations from the website. It means only that the occupation-composition counterfactual for that quarter is unavailable under the current CPS design.

# May-2025 OEWS external robustness route — provenance decision

Status: **REJECTED AS AN INPUT TO GENAI-AT-WORK COMPOSITION RESULTS**.

The public repository `farach/onet-vintage-bias-public` contains a real derived file,
`analysis/canonical/tables/oews_weight_sensitivity.csv`, and its bridge script states that it uses
fixed May-2025 OEWS staffing. The script constructs employment-weighted sector exposure at detailed
SOC-6 level and uses published OEWS employment relative standard errors for a weight-sensitivity envelope.

However, that repository explicitly does not redistribute the OEWS staffing input, and its shared helper
terminates when non-distributed support files/inputs are absent. The public archive therefore supports
inspection of the method and its derived outputs, not independent recovery of the exact sector × occupation
staffing matrix needed here.

Consequences for this project:

1. Do not import its `oews_weight_sensitivity.csv` as a composition matrix.
2. Do not infer GenAI occupation-adjusted industry residuals from its sector exposure outputs.
3. Retain it only as methodological evidence that a May-2025 OEWS detailed-SOC sector bridge is feasible.
4. Execute our own OEWS robustness analysis only when the official staffing input is independently obtained
   and checksummed, with a separately reviewed RPS-industry mapping.

This prevents a derived result from another study from silently becoming an undocumented input here.

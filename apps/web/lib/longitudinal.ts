import fs from "node:fs/promises";
import path from "node:path";

export type QuarterDiagnostic = {
  increment_A_given_H: number;
  increment_H_given_A: number;
  loo_A_beats_H: number;
  loo_H_beats_A: number;
  loo_H_minus_A_max: number;
  loo_H_minus_A_min: number;
  n: number;
  r2_H_A: number;
  r2_S_A: number;
  r2_S_H: number;
  r2_S_A_H: number;
  r_A_H: number;
  spearman_A_H: number;
};

export type RankStability = {
  consecutive: [string, string, number][];
  endpoint: number;
  max_pairwise: number;
  median_pairwise: number;
  min_pairwise: number;
};

export type CrossLevelComparison = {
  industry_H_minus_A_for_S_r2: number;
  industry_incremental_H_given_A_r2: number;
  occupation_A_minus_H_for_S_r2: number;
  occupation_incremental_H_given_A_r2: number;
  occupation_minus_industry_pearson_A_H: number;
  occupation_minus_industry_spearman_A_H: number;
};

export type LongitudinalDiagnostics = {
  schema_version: number;
  source_content_sha256: string;
  input_scope: {
    industry_entities: number;
    occupation_entities: number;
    metrics: string[];
    periods: string[];
    subgroup_series: number;
  };
  interpretive_guardrails: string[];
  cross_level_comparison: Record<string, CrossLevelComparison>;
  quarter_diagnostics: {
    industry: Record<string, QuarterDiagnostic>;
    occupation: Record<string, QuarterDiagnostic>;
  };
  rank_stability: {
    industry: Record<"A" | "H" | "S", RankStability>;
    occupation: Record<"A" | "H" | "S", RankStability>;
  };
  rank_stability_dominance: {
    industry: {
      adoption_rank_corr_gt_assisted_hours_rank_corr: number;
      adoption_rank_corr_gt_reported_savings_rank_corr: number;
      quarter_pairs: number;
      reported_savings_rank_corr_gt_assisted_hours_rank_corr: number;
    };
    occupation: {
      adoption_rank_corr_gt_assisted_hours_rank_corr: number;
      adoption_rank_corr_gt_reported_savings_rank_corr: number;
      quarter_pairs: number;
      reported_savings_rank_corr_gt_assisted_hours_rank_corr: number;
    };
  };
  status: string;
};

export async function loadLongitudinalDiagnostics(): Promise<LongitudinalDiagnostics> {
  const file = path.join(
    process.cwd(),
    "..",
    "..",
    "data",
    "derived",
    "longitudinal",
    "longitudinal_diagnostics.json",
  );
  return JSON.parse(await fs.readFile(file, "utf8")) as LongitudinalDiagnostics;
}

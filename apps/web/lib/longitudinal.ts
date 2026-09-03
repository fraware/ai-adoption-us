import fs from "node:fs/promises";
import path from "node:path";
import { readCurrentReleaseJsonArtifact } from "./release";

const LONGITUDINAL_ARTIFACT_ID = "rps-longitudinal-diagnostics";
const RPS_SOURCE_ID = "rps-genai-tracker-fred-release-6";
const SHA256_RE = /^[0-9a-f]{64}$/;

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

type RankDominance = {
  adoption_rank_corr_gt_assisted_hours_rank_corr: number;
  adoption_rank_corr_gt_reported_savings_rank_corr: number;
  quarter_pairs: number;
  reported_savings_rank_corr_gt_assisted_hours_rank_corr: number;
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
    industry: RankDominance;
    occupation: RankDominance;
  };
  status: string;
};

function sameKeys(record: Record<string, unknown>, periods: string[]): boolean {
  const actual = Object.keys(record).sort();
  const expected = [...periods].sort();
  return actual.length === expected.length && actual.every((value, index) => value === expected[index]);
}

function validateDiagnostics(value: LongitudinalDiagnostics): void {
  const periods = value.input_scope?.periods;
  if (
    value.schema_version !== 1 ||
    typeof value.source_content_sha256 !== "string" ||
    !SHA256_RE.test(value.source_content_sha256) ||
    !Array.isArray(periods) ||
    periods.length < 2 ||
    value.input_scope.industry_entities !== 20 ||
    value.input_scope.occupation_entities !== 22 ||
    value.input_scope.subgroup_series !== 126 ||
    !Array.isArray(value.input_scope.metrics) ||
    value.input_scope.metrics.length !== 3
  ) {
    throw new Error("Longitudinal diagnostics violate the Observatory release contract");
  }

  if (
    !sameKeys(value.cross_level_comparison, periods) ||
    !sameKeys(value.quarter_diagnostics.industry, periods) ||
    !sameKeys(value.quarter_diagnostics.occupation, periods)
  ) {
    throw new Error("Longitudinal diagnostic periods are internally inconsistent");
  }

  const expectedPairs = (periods.length * (periods.length - 1)) / 2;
  for (const entityType of ["industry", "occupation"] as const) {
    const dominance = value.rank_stability_dominance[entityType];
    if (dominance.quarter_pairs !== expectedPairs) {
      throw new Error(`Rank-stability pair count is invalid for ${entityType}`);
    }
    for (const count of [
      dominance.adoption_rank_corr_gt_assisted_hours_rank_corr,
      dominance.adoption_rank_corr_gt_reported_savings_rank_corr,
      dominance.reported_savings_rank_corr_gt_assisted_hours_rank_corr,
    ]) {
      if (!Number.isInteger(count) || count < 0 || count > expectedPairs) {
        throw new Error(`Rank-stability dominance count is invalid for ${entityType}`);
      }
    }
  }
}

async function loadRepositoryFallback(): Promise<LongitudinalDiagnostics> {
  const file = path.join(
    process.cwd(),
    "..",
    "..",
    "data",
    "derived",
    "longitudinal",
    "longitudinal_diagnostics.json",
  );
  const value = JSON.parse(await fs.readFile(file, "utf8")) as LongitudinalDiagnostics;
  validateDiagnostics(value);
  return value;
}

export async function loadLongitudinalDiagnostics(): Promise<LongitudinalDiagnostics> {
  if (process.env.DATA_MODE === "derived_only") {
    const result = await readCurrentReleaseJsonArtifact<LongitudinalDiagnostics>(
      LONGITUDINAL_ARTIFACT_ID,
    );
    if (result !== null) {
      validateDiagnostics(result.value);
      const sources = result.release.manifest.sources.filter(
        (source) => source.source_id === RPS_SOURCE_ID,
      );
      if (
        sources.length !== 1 ||
        sources[0].source_vintage_id !== `sha256:${result.value.source_content_sha256}`
      ) {
        throw new Error("Longitudinal diagnostics are not bound to the promoted RPS source vintage");
      }
      return result.value;
    }
  }

  return loadRepositoryFallback();
}

import fs from "node:fs/promises";
import path from "node:path";

type TriangulationPair = {
  entity_index: number;
  entity_name: string;
  comparability: "primary" | "limited";
  btos_estimate_pct: number;
  rps_adoption_work_pct: number;
  included_primary: boolean;
  included_expanded_sensitivity: boolean;
};

type TriangulationSummary = {
  n: number;
  spearman_rho: number;
  pearson_r: number;
};

export type BtosRpsTriangulation = {
  analysis_id: string;
  primary: TriangulationSummary & { entity_indices: number[] };
  expanded_sensitivity: TriangulationSummary & { added_entity_indices: number[] };
  pairs: TriangulationPair[];
  public_product_status: string;
};

export async function loadBtosRpsTriangulation(): Promise<BtosRpsTriangulation> {
  const file = path.join(
    process.cwd(),
    "..",
    "..",
    "data",
    "derived",
    "btos_rps",
    "industry_triangulation_q2_2026_v1.json",
  );
  const parsed = JSON.parse(await fs.readFile(file, "utf8")) as BtosRpsTriangulation;

  if (parsed.analysis_id !== "btos-rps-industry-triangulation-q2-2026-v1") {
    throw new Error(`Unexpected BTOS-RPS analysis id: ${parsed.analysis_id}`);
  }
  if (parsed.primary.n !== 14 || parsed.expanded_sensitivity.n !== 17) {
    throw new Error(
      `Unexpected BTOS-RPS sample sizes: primary=${parsed.primary.n}, expanded=${parsed.expanded_sensitivity.n}`,
    );
  }
  if (parsed.pairs.filter((row) => row.included_primary).length !== parsed.primary.n) {
    throw new Error("BTOS-RPS primary pair count does not match the canonical analysis summary");
  }
  if (
    parsed.pairs.filter((row) => row.included_expanded_sensitivity).length !==
    parsed.expanded_sensitivity.n
  ) {
    throw new Error("BTOS-RPS expanded pair count does not match the canonical analysis summary");
  }

  return parsed;
}

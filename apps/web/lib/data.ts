import fs from "node:fs/promises";
import path from "node:path";
import { readCurrentReleaseJsonArtifact } from "./release";
import type { EntityType, Observation } from "./types";

const EXPECTED_ENTITY_COUNTS = { industry: 20, occupation: 22 } as const;
const RPS_SOURCE_ID = "rps-genai-tracker-fred-release-6";
const PUBLIC_VIEW_ARTIFACT_ID = "rps-public-observation-view";
const PUBLIC_VIEW_CONTRACT_ID = "rps-public-observation-delivery-v1";
const NATIONAL_METRICS = new Set([
  "adoption_work",
  "work_use_last_week",
  "work_use_daily",
  "assisted_hours_share",
  "reported_time_savings_share",
]);
const SUBGROUP_METRICS = new Set([
  "adoption_work",
  "assisted_hours_share",
  "reported_time_savings_share",
]);

type SourceSeriesRecord = {
  entity_type: "national" | "industry" | "occupation";
  entity_id: string;
  entity_name: string;
};

type SourceSeriesManifest = {
  series: SourceSeriesRecord[];
};

type AuditRecord = {
  series_id: string;
  metric_id: string;
  entity_id: string;
  entity_type: "industry" | "occupation";
  period: string;
  value: number;
};

type PublicObservationRow = {
  date: string;
  entity_id: string;
  entity_name: string;
  entity_type: EntityType;
  metric_id: string;
  period: string;
  series_id: string;
  source_url: string;
  unit: "Percent";
  value: number;
};

type PublicObservationView = {
  schema_version: number;
  view_contract_id: string;
  source_id: string;
  source_vintage_id: string;
  publication_scope: string;
  source_input_bytes_included: boolean;
  generic_query_api_included: boolean;
  historical_subgroup_panel_included: boolean;
  latest_subgroup_period: string;
  national_complete_periods: string[];
  national_history: PublicObservationRow[];
  industry_latest: PublicObservationRow[];
  occupation_latest: PublicObservationRow[];
};

function periodToDate(period: string): string {
  const [yearText, quarterText] = period.split("-Q");
  const month = ({ "1": "01", "2": "04", "3": "07", "4": "10" } as const)[
    quarterText as "1" | "2" | "3" | "4"
  ];
  if (!month) throw new Error(`Unsupported quarter: ${period}`);
  return `${yearText}-${month}-01`;
}

async function loadAuditSnapshot(): Promise<Observation[]> {
  const file = path.join(
    process.cwd(),
    "..",
    "..",
    "data",
    "audit",
    "private",
    "rps_subgroup_5q_audit.json",
  );
  const parsed = JSON.parse(await fs.readFile(file, "utf8")) as { records: AuditRecord[] };
  return parsed.records.map((row) => ({
    source: "fred_rps",
    series_id: row.series_id,
    metric_id: row.metric_id,
    entity_id: row.entity_id,
    entity_type: row.entity_type,
    date: periodToDate(row.period),
    period: row.period,
    value: row.value,
    unit: "Percent",
    ingested_at_utc: "private-audit-reviewed-2026-08-30",
  }));
}

function assertPublicRow(
  row: PublicObservationRow,
  expectedType: EntityType,
  expectedMetrics: Set<string>,
  expectedPeriod: string | null,
): void {
  if (
    row.entity_type !== expectedType ||
    typeof row.entity_id !== "string" ||
    row.entity_id.length === 0 ||
    typeof row.entity_name !== "string" ||
    row.entity_name.length === 0 ||
    typeof row.series_id !== "string" ||
    row.series_id.length === 0 ||
    typeof row.metric_id !== "string" ||
    !expectedMetrics.has(row.metric_id) ||
    typeof row.date !== "string" ||
    typeof row.period !== "string" ||
    row.unit !== "Percent" ||
    typeof row.value !== "number" ||
    !Number.isFinite(row.value) ||
    row.value < 0 ||
    row.value > 100
  ) {
    throw new Error(`Invalid bounded RPS public observation: ${JSON.stringify(row)}`);
  }
  if (expectedPeriod !== null && row.period !== expectedPeriod) {
    throw new Error(`Bounded RPS public observation uses unexpected period: ${row.period}`);
  }
}

function validatePublicView(view: PublicObservationView): void {
  if (
    view.schema_version !== 1 ||
    view.view_contract_id !== PUBLIC_VIEW_CONTRACT_ID ||
    view.source_id !== RPS_SOURCE_ID ||
    view.publication_scope !== "selected_attributed_aggregate_views" ||
    view.source_input_bytes_included !== false ||
    view.generic_query_api_included !== false ||
    view.historical_subgroup_panel_included !== false
  ) {
    throw new Error("Promoted RPS public observation view violates its release contract");
  }
  if (
    !Array.isArray(view.national_complete_periods) ||
    view.national_complete_periods.length === 0 ||
    !Array.isArray(view.national_history) ||
    !Array.isArray(view.industry_latest) ||
    !Array.isArray(view.occupation_latest)
  ) {
    throw new Error("Promoted RPS public observation view has an invalid row structure");
  }

  const nationalPeriods = new Set(view.national_complete_periods);
  if (view.national_history.length !== nationalPeriods.size * NATIONAL_METRICS.size) {
    throw new Error("Promoted RPS national history does not contain one complete metric family per period");
  }
  const nationalKeys = new Set<string>();
  for (const row of view.national_history) {
    assertPublicRow(row, "national", NATIONAL_METRICS, null);
    if (row.entity_id !== "us" || !nationalPeriods.has(row.period)) {
      throw new Error("Promoted RPS national history contains an unexpected entity or period");
    }
    const key = `${row.period}:${row.metric_id}`;
    if (nationalKeys.has(key)) throw new Error(`Duplicate bounded national observation: ${key}`);
    nationalKeys.add(key);
  }

  const subgroupSpecs: Array<{
    rows: PublicObservationRow[];
    type: "industry" | "occupation";
    count: number;
  }> = [
    { rows: view.industry_latest, type: "industry", count: EXPECTED_ENTITY_COUNTS.industry },
    { rows: view.occupation_latest, type: "occupation", count: EXPECTED_ENTITY_COUNTS.occupation },
  ];
  for (const spec of subgroupSpecs) {
    if (spec.rows.length !== spec.count * SUBGROUP_METRICS.size) {
      throw new Error(`Promoted RPS ${spec.type} view has incomplete entity/metric coverage`);
    }
    const keys = new Set<string>();
    const entities = new Set<string>();
    for (const row of spec.rows) {
      assertPublicRow(row, spec.type, SUBGROUP_METRICS, view.latest_subgroup_period);
      const key = `${row.entity_id}:${row.metric_id}`;
      if (keys.has(key)) throw new Error(`Duplicate bounded ${spec.type} observation: ${key}`);
      keys.add(key);
      entities.add(row.entity_id);
    }
    if (entities.size !== spec.count) {
      throw new Error(`Promoted RPS ${spec.type} view has incomplete entity coverage`);
    }
  }
}

function toObservation(row: PublicObservationRow, retrievedAt: string): Observation {
  return {
    source: "fred_rps",
    series_id: row.series_id,
    metric_id: row.metric_id,
    entity_id: row.entity_id,
    entity_type: row.entity_type,
    date: row.date,
    period: row.period,
    value: row.value,
    unit: row.unit,
    ingested_at_utc: retrievedAt,
  };
}

async function loadPromotedPublicView(): Promise<Observation[]> {
  const result = await readCurrentReleaseJsonArtifact<PublicObservationView>(PUBLIC_VIEW_ARTIFACT_ID);
  if (result === null) return [];
  validatePublicView(result.value);

  const sources = result.release.manifest.sources.filter((source) => source.source_id === RPS_SOURCE_ID);
  if (sources.length !== 1) {
    throw new Error("Promoted release must contain exactly one RPS source record");
  }
  const source = sources[0];
  if (source.source_vintage_id !== result.value.source_vintage_id || !source.retrieved_at) {
    throw new Error("Bounded RPS public view is not bound to the promoted release source vintage");
  }

  return [
    ...result.value.national_history,
    ...result.value.industry_latest,
    ...result.value.occupation_latest,
  ].map((row) => toObservation(row, source.retrieved_at));
}

async function loadFredLiveNoStore(): Promise<Observation[]> {
  const apiKey = process.env.FRED_API_KEY;
  if (!apiKey) throw new Error("FRED_API_KEY is required for DATA_MODE=fred_live_no_store");
  throw new Error(
    "fred_live_no_store remains a separately governed server-side adapter and is not enabled by the public release path.",
  );
}

export async function loadObservations(): Promise<Observation[]> {
  const mode = process.env.DATA_MODE;
  if (mode === "audit_snapshot") return loadAuditSnapshot();
  if (mode === "fred_live_no_store") return loadFredLiveNoStore();
  if (mode === "derived_only") return loadPromotedPublicView();
  throw new Error(
    "DATA_MODE must be explicitly set to audit_snapshot, fred_live_no_store, or derived_only",
  );
}

export function latestNational(rows: Observation[]): Map<string, Observation> {
  const selected = rows.filter((row) => row.entity_id === "us");
  const out = new Map<string, Observation>();
  for (const row of selected) {
    const current = out.get(row.metric_id);
    if (!current || row.date > current.date) out.set(row.metric_id, row);
  }
  return out;
}

export function latestCommonPeriod(
  rows: Observation[],
  entityType: "industry" | "occupation",
  metrics: string[],
): string | null {
  const coverage = new Map<string, Map<string, Set<string>>>();
  for (const row of rows) {
    if (row.entity_type !== entityType || !metrics.includes(row.metric_id)) continue;
    if (!coverage.has(row.period)) coverage.set(row.period, new Map());
    const byEntity = coverage.get(row.period)!;
    if (!byEntity.has(row.entity_id)) byEntity.set(row.entity_id, new Set());
    byEntity.get(row.entity_id)!.add(row.metric_id);
  }

  const expected = EXPECTED_ENTITY_COUNTS[entityType];
  const valid = [...coverage.entries()]
    .filter(
      ([, entities]) =>
        entities.size === expected &&
        [...entities.values()].every((seen) => metrics.every((metric) => seen.has(metric))),
    )
    .map(([period]) => period)
    .sort();
  return valid.at(-1) ?? null;
}

export function wideEntityRows(
  rows: Observation[],
  entityType: "industry" | "occupation",
  period: string,
  metrics: string[],
): Array<{ entityId: string; values: Record<string, number> }> {
  const byEntity = new Map<string, Record<string, number>>();
  for (const row of rows) {
    if (row.entity_type !== entityType || row.period !== period || !metrics.includes(row.metric_id)) continue;
    const values = byEntity.get(row.entity_id) ?? {};
    values[row.metric_id] = row.value;
    byEntity.set(row.entity_id, values);
  }
  const complete = [...byEntity.entries()]
    .filter(([, values]) => metrics.every((metric) => values[metric] !== undefined))
    .map(([entityId, values]) => ({ entityId, values }));
  if (complete.length !== EXPECTED_ENTITY_COUNTS[entityType]) return [];
  return complete;
}

export async function loadEntityNames(
  entityType: "industry" | "occupation",
): Promise<Map<string, string>> {
  const file = path.join(
    process.cwd(),
    "..",
    "..",
    "data",
    "registry",
    "rps_source_series_manifest.json",
  );
  const parsed = JSON.parse(await fs.readFile(file, "utf8")) as SourceSeriesManifest;
  const names = new Map<string, string>();
  for (const row of parsed.series) {
    if (row.entity_type === entityType) names.set(row.entity_id, row.entity_name);
  }
  const expected = EXPECTED_ENTITY_COUNTS[entityType];
  if (names.size !== expected) {
    throw new Error(`Expected ${expected} ${entityType} entity names, found ${names.size}`);
  }
  return names;
}

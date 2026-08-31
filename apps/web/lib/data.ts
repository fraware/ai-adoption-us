import fs from "node:fs/promises";
import path from "node:path";
import type { Observation } from "./types";

const EXPECTED_ENTITY_COUNTS = { industry: 20, occupation: 22 } as const;



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

function periodToDate(period: string): string {
  const [yearText, quarterText] = period.split("-Q");
  const month = ({ "1": "01", "2": "04", "3": "07", "4": "10" } as const)[quarterText as "1" | "2" | "3" | "4"];
  if (!month) throw new Error(`Unsupported quarter: ${period}`);
  return `${yearText}-${month}-01`;
}

async function loadAuditSnapshot(): Promise<Observation[]> {
  const file = path.join(process.cwd(), "..", "..", "data", "audit", "private", "rps_subgroup_5q_audit.json");
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

async function loadFredLiveNoStore(): Promise<Observation[]> {
  const apiKey = process.env.FRED_API_KEY;
  if (!apiKey) throw new Error("FRED_API_KEY is required for DATA_MODE=fred_live_no_store");
  throw new Error(
    "fred_live_no_store is intentionally not enabled in this reconstruction candidate. " +
    "Complete a fresh source-terms review and implement the reviewed server-side adapter before deployment.",
  );
}

export async function loadObservations(): Promise<Observation[]> {
  const mode = process.env.DATA_MODE;
  if (mode === "audit_snapshot") return loadAuditSnapshot();
  if (mode === "fred_live_no_store") return loadFredLiveNoStore();
  if (mode === "derived_only") return [];
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
    .filter(([, entities]) =>
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

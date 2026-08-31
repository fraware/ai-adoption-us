export type EntityType = "national" | "industry" | "occupation";

export type Observation = {
  source: "fred_rps";
  series_id: string;
  metric_id: string;
  entity_id: string;
  entity_type: EntityType;
  date: string;
  period: string;
  value: number;
  unit: "Percent";
  realtime_start?: string | null;
  realtime_end?: string | null;
  ingested_at_utc: string;
  source_last_updated?: string | null;
};

#!/usr/bin/env node

import { readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const directory = process.argv[2] ?? "qa-results/lighthouse";
const minimumAccessibility = Number(process.env.MIN_LIGHTHOUSE_ACCESSIBILITY ?? "0.95");

const files = (await readdir(directory))
  .filter((name) => name.endsWith(".json") && !name.endsWith("summary.json"))
  .sort();

if (files.length === 0) {
  throw new Error(`No Lighthouse JSON reports found in ${directory}`);
}

const rows = [];
let failed = false;

for (const file of files) {
  const report = JSON.parse(await readFile(path.join(directory, file), "utf8"));
  const accessibility = report.categories?.accessibility?.score ?? null;
  const performance = report.categories?.performance?.score ?? null;
  const auditValue = (id) => report.audits?.[id]?.numericValue ?? null;

  if (typeof accessibility !== "number" || accessibility < minimumAccessibility) {
    failed = true;
  }

  rows.push({
    file,
    finalUrl: report.finalUrl ?? null,
    userAgent: report.userAgent ?? null,
    lighthouseVersion: report.lighthouseVersion ?? null,
    accessibility,
    performance,
    firstContentfulPaintMs: auditValue("first-contentful-paint"),
    largestContentfulPaintMs: auditValue("largest-contentful-paint"),
    totalBlockingTimeMs: auditValue("total-blocking-time"),
    cumulativeLayoutShift: auditValue("cumulative-layout-shift"),
    speedIndexMs: auditValue("speed-index"),
  });
}

const summary = {
  minimumAccessibility,
  performanceThreshold: null,
  performanceInterpretation:
    "Recorded as CI lab evidence only; no launch pass/fail threshold is imposed because CI performance is not field Core Web Vitals.",
  reports: rows,
};

await writeFile(
  path.join(directory, "lighthouse-summary.json"),
  `${JSON.stringify(summary, null, 2)}\n`,
);

const markdown = [
  "# Lighthouse automated QA summary",
  "",
  `Accessibility gate: **>= ${(minimumAccessibility * 100).toFixed(0)}**.`,
  "",
  "Performance scores and lab metrics are recorded for regression review only; they are not treated as field Core Web Vitals.",
  "",
  "| Report | Accessibility | Performance | LCP (ms) | CLS | TBT (ms) |",
  "|---|---:|---:|---:|---:|---:|",
  ...rows.map((row) => {
    const pct = (value) => (typeof value === "number" ? (value * 100).toFixed(0) : "n/a");
    const number = (value, digits = 0) =>
      typeof value === "number" ? value.toFixed(digits) : "n/a";
    return `| ${row.file} | ${pct(row.accessibility)} | ${pct(row.performance)} | ${number(row.largestContentfulPaintMs)} | ${number(row.cumulativeLayoutShift, 3)} | ${number(row.totalBlockingTimeMs)} |`;
  }),
  "",
].join("\n");

await writeFile(path.join(directory, "lighthouse-summary.md"), markdown);

console.log(markdown);

if (failed) {
  console.error(`Lighthouse accessibility score below ${minimumAccessibility} in at least one report.`);
  process.exitCode = 1;
}

#!/usr/bin/env node

import { mkdir, writeFile } from "node:fs/promises";
import { chromium, firefox, webkit } from "playwright";

const outputDirectory = process.argv[2] ?? "qa-results";
await mkdir(outputDirectory, { recursive: true });

const launchers = [
  ["chrome", () => chromium.launch({ channel: "chrome", headless: true })],
  ["firefox", () => firefox.launch({ headless: true })],
  ["webkit", () => webkit.launch({ headless: true })],
];

const browsers = [];
for (const [name, launch] of launchers) {
  const browser = await launch();
  try {
    browsers.push({ name, version: browser.version() });
  } finally {
    await browser.close();
  }
}

const report = {
  generatedAtUtc: new Date().toISOString(),
  playwrightVersion: process.env.npm_package_devDependencies__playwright_test ?? null,
  browsers,
  interpretation: {
    chrome: "Stable Chrome channel installed on the GitHub-hosted Ubuntu runner.",
    firefox: "Playwright-managed Firefox build.",
    webkit:
      "Playwright WebKit is an engine-level compatibility check only; it is not evidence of real Safari or iOS Safari completion.",
  },
};

await writeFile(
  `${outputDirectory}/browser-versions.json`,
  `${JSON.stringify(report, null, 2)}\n`,
);
console.log(JSON.stringify(report, null, 2));

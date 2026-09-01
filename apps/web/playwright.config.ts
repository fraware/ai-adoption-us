import { defineConfig } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";

const projects = [
  { name: "chromium-375", browserName: "chromium" as const, viewport: { width: 375, height: 812 } },
  { name: "chromium-768", browserName: "chromium" as const, viewport: { width: 768, height: 1024 } },
  { name: "chromium-1024", browserName: "chromium" as const, viewport: { width: 1024, height: 900 } },
  { name: "chromium-1440", browserName: "chromium" as const, viewport: { width: 1440, height: 1000 } },
  { name: "firefox-375", browserName: "firefox" as const, viewport: { width: 375, height: 812 } },
  { name: "firefox-1440", browserName: "firefox" as const, viewport: { width: 1440, height: 1000 } },
  { name: "webkit-375", browserName: "webkit" as const, viewport: { width: 375, height: 812 } },
  { name: "webkit-1440", browserName: "webkit" as const, viewport: { width: 1440, height: 1000 } },
];

export default defineConfig({
  testDir: "./tests/browser",
  outputDir: "qa-results/test-results",
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 4 : undefined,
  reporter: [
    ["list"],
    ["json", { outputFile: "qa-results/playwright-results.json" }],
    ["html", { outputFolder: "qa-results/playwright-html", open: "never" }],
  ],
  use: {
    baseURL,
    colorScheme: "light",
    screenshot: "on",
    trace: "retain-on-failure",
  },
  projects: projects.map((project) => ({
    name: project.name,
    use: {
      browserName: project.browserName,
      viewport: project.viewport,
    },
  })),
});

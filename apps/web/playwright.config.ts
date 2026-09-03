import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";

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
  projects: [
    {
      name: "chrome-375",
      use: {
        browserName: "chromium",
        channel: "chrome",
        viewport: { width: 375, height: 812 },
      },
    },
    {
      name: "chrome-768",
      use: {
        browserName: "chromium",
        channel: "chrome",
        viewport: { width: 768, height: 1024 },
      },
    },
    {
      name: "chrome-1024",
      use: {
        browserName: "chromium",
        channel: "chrome",
        viewport: { width: 1024, height: 900 },
      },
    },
    {
      name: "chrome-1440",
      use: {
        browserName: "chromium",
        channel: "chrome",
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: "firefox-375",
      use: {
        browserName: "firefox",
        viewport: { width: 375, height: 812 },
      },
    },
    {
      name: "firefox-1440",
      use: {
        browserName: "firefox",
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: "webkit-375",
      use: {
        browserName: "webkit",
        viewport: { width: 375, height: 812 },
      },
    },
    {
      name: "webkit-1440",
      use: {
        browserName: "webkit",
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: "android-chrome-pixel-7-emulation",
      use: {
        ...devices["Pixel 7"],
        browserName: "chromium",
        channel: "chrome",
      },
    },
    {
      name: "ios-webkit-iphone-15-pro-emulation",
      use: {
        ...devices["iPhone 15 Pro"],
        browserName: "webkit",
      },
    },
  ],
});

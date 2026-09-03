#!/usr/bin/env node

import { mkdir, readFile, writeFile } from "node:fs/promises";
import { chromium, devices, firefox, webkit } from "playwright";

const outputDirectory = process.argv[2] ?? "qa-results";
await mkdir(outputDirectory, { recursive: true });

const packageJson = JSON.parse(
  await readFile(new URL("../package.json", import.meta.url), "utf8"),
);
const playwrightVersion = packageJson.devDependencies?.["@playwright/test"] ?? null;
if (!playwrightVersion) {
  throw new Error("Unable to resolve pinned @playwright/test version from package.json");
}

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

function deviceSummary(projectName, descriptorName, browser) {
  const descriptor = devices[descriptorName];
  if (!descriptor) {
    throw new Error(`Unable to resolve Playwright device descriptor: ${descriptorName}`);
  }
  return {
    projectName,
    descriptorName,
    browser,
    viewport: descriptor.viewport,
    screen: descriptor.screen,
    deviceScaleFactor: descriptor.deviceScaleFactor,
    isMobile: descriptor.isMobile,
    hasTouch: descriptor.hasTouch,
  };
}

const mobileEmulations = [
  deviceSummary("android-chrome-pixel-7-emulation", "Pixel 7", "stable Chrome channel"),
  deviceSummary("ios-webkit-iphone-15-pro-emulation", "iPhone 15 Pro", "Playwright WebKit"),
];

const report = {
  generatedAtUtc: new Date().toISOString(),
  playwrightVersion,
  browsers,
  mobileEmulations,
  interpretation: {
    chrome: "Stable Chrome channel installed on the GitHub-hosted Ubuntu runner.",
    firefox: "Playwright-managed Firefox build.",
    webkit:
      "Playwright WebKit is an engine-level compatibility check only; it is not evidence of real Safari or native iOS Safari completion.",
    androidEmulation:
      "Pixel 7 device-context emulation runs against the stable Chrome binary; it is a defensible automated Android/Chrome proxy, not a physical Android-device test.",
    iosEmulation:
      "iPhone 15 Pro device-context emulation runs against Playwright WebKit; it is a defensible automated iOS/WebKit proxy, not native iOS Safari or a physical iPhone test.",
  },
};

await writeFile(
  `${outputDirectory}/browser-versions.json`,
  `${JSON.stringify(report, null, 2)}\n`,
);
console.log(JSON.stringify(report, null, 2));

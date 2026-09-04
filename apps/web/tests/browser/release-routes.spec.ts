import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const routes = [
  { slug: "home", path: "/" },
  { slug: "explore", path: "/explore" },
  { slug: "industries", path: "/explore/industries" },
  { slug: "occupations", path: "/explore/occupations" },
  { slug: "methodology", path: "/methodology" },
  { slug: "sources", path: "/sources" },
  { slug: "after-adoption", path: "/blog/after-adoption" },
] as const;

const primaryNavigation = [
  "/explore",
  "/blog/after-adoption",
  "/methodology",
] as const;

const ANDROID_PROJECT = "android-chrome-pixel-7-emulation";
const IOS_PROJECT = "ios-webkit-iphone-15-pro-emulation";
const EXPECTED_404_CONSOLE_ERROR =
  "Failed to load resource: the server responded with a status of 404 (Not Found)";

async function assertMobileEmulationContract(page: Page) {
  const projectName = test.info().project.name;
  if (projectName !== ANDROID_PROJECT && projectName !== IOS_PROJECT) {
    return;
  }

  const environment = await page.evaluate(() => ({
    userAgent: navigator.userAgent,
    innerWidth: window.innerWidth,
  }));

  expect(environment.innerWidth, `${projectName} must remain a phone-width context`).toBeLessThanOrEqual(450);

  if (projectName === ANDROID_PROJECT) {
    expect(environment.userAgent).toContain("Android");
  } else {
    expect(environment.userAgent).toContain("iPhone");
  }

  await page.evaluate(() => {
    document.documentElement.dataset.qaTouchStartSeen = "false";
    window.addEventListener(
      "touchstart",
      () => {
        document.documentElement.dataset.qaTouchStartSeen = "true";
      },
      { once: true },
    );
  });
  await page.touchscreen.tap(12, 12);
  await expect(
    page.locator("html"),
    `${projectName} must deliver an emulated touchstart event`,
  ).toHaveAttribute("data-qa-touch-start-seen", "true");
  await page.evaluate(() => {
    delete document.documentElement.dataset.qaTouchStartSeen;
  });
}

test.describe("Release 1 rendered browser QA", () => {
  for (const route of routes) {
    test(`${route.slug}: semantics, keyboard, responsive and axe contract`, async ({ page }) => {
      const consoleErrors: string[] = [];
      const pageErrors: string[] = [];

      page.on("console", (message) => {
        if (message.type() === "error") {
          consoleErrors.push(message.text());
        }
      });
      page.on("pageerror", (error) => pageErrors.push(error.message));

      const response = await page.goto(route.path, { waitUntil: "networkidle" });
      expect(response, `No document response for ${route.path}`).not.toBeNull();
      expect(response?.ok(), `HTTP ${response?.status()} for ${route.path}`).toBeTruthy();

      const icon = page.locator('link[rel~="icon"]').first();
      await expect(icon, `No application icon metadata on ${route.path}`).toHaveCount(1);
      const iconHref = await icon.getAttribute("href");
      expect(iconHref, `Application icon has no href on ${route.path}`).toBeTruthy();
      const iconResponse = await page.request.get(new URL(iconHref!, page.url()).toString());
      expect(iconResponse.ok(), `Application icon failed to load on ${route.path}`).toBeTruthy();

      await expect(page.locator("main")).toHaveCount(1);
      await expect(page.locator("h1")).toHaveCount(1);
      await expect(page.getByRole("navigation", { name: "Primary navigation" })).toHaveCount(1);
      await expect(page.locator("footer.site-footer")).toHaveCount(1);

      for (const href of primaryNavigation) {
        await expect(page.locator(`nav[aria-label="Primary navigation"] a[href="${href}"]`)).toHaveCount(1);
      }

      const pageOverflow = await page.evaluate(() => ({
        clientWidth: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
      }));
      expect(
        pageOverflow.scrollWidth,
        `Page-level horizontal overflow on ${route.path}: ${JSON.stringify(pageOverflow)}`,
      ).toBeLessThanOrEqual(pageOverflow.clientWidth + 1);

      const visibleTables = page.locator("table:visible");
      const tableCount = await visibleTables.count();
      for (let index = 0; index < tableCount; index += 1) {
        const table = visibleTables.nth(index);
        await expect(table).toBeVisible();
        await expect(
          table.locator(
            "xpath=ancestor::*[contains(concat(' ', normalize-space(@class), ' '), ' table-wrap ')][1]",
          ),
        ).toHaveCount(1);
      }

      await page.keyboard.press("Tab");
      const skipLink = page.locator(".skip-link");
      await expect(skipLink).toBeFocused();
      await expect(skipLink).toBeVisible();
      const focusStyle = await skipLink.evaluate((element) => {
        const style = getComputedStyle(element);
        return {
          outlineStyle: style.outlineStyle,
          outlineWidth: style.outlineWidth,
        };
      });
      expect(focusStyle.outlineStyle).not.toBe("none");
      expect(Number.parseFloat(focusStyle.outlineWidth)).toBeGreaterThanOrEqual(2);

      await page.keyboard.press("Enter");
      await expect(page.locator("#main-content")).toBeFocused();

      await page.emulateMedia({ reducedMotion: "reduce" });
      const reducedMotion = await page.evaluate(() => {
        const skip = document.querySelector(".skip-link");
        return {
          htmlScrollBehavior: getComputedStyle(document.documentElement).scrollBehavior,
          skipTransitionDuration: skip ? getComputedStyle(skip).transitionDuration : null,
        };
      });
      expect(reducedMotion.htmlScrollBehavior).toBe("auto");
      expect(reducedMotion.skipTransitionDuration).toBe("0s");

      const accessibility = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
        .analyze();
      const severeViolations = accessibility.violations.filter(
        (violation) => violation.impact === "critical" || violation.impact === "serious",
      );
      expect(
        severeViolations,
        `Serious/critical axe violations on ${route.path}: ${JSON.stringify(severeViolations, null, 2)}`,
      ).toEqual([]);

      await assertMobileEmulationContract(page);

      expect(pageErrors, `Uncaught runtime errors on ${route.path}`).toEqual([]);
      expect(consoleErrors, `Console errors on ${route.path}`).toEqual([]);
    });
  }

  test("primary navigation links perform real end-to-end route transitions", async ({ page }) => {
    const response = await page.goto("/", { waitUntil: "networkidle" });
    expect(response, "No initial home document response").not.toBeNull();
    expect(response?.ok(), `Initial home HTTP ${response?.status()}`).toBeTruthy();

    for (const href of primaryNavigation) {
      const link = page.locator(`nav[aria-label="Primary navigation"] a[href="${href}"]`);
      await expect(link).toBeVisible();
      await link.click();
      await expect.poll(() => new URL(page.url()).pathname).toBe(href);
      await expect(page.locator("main")).toHaveCount(1);
      await expect(page.locator("h1")).toHaveCount(1);

      const homeLink = page.locator('a.brand[href="/"]');
      await expect(homeLink).toBeVisible();
      await homeLink.click();
      await expect.poll(() => new URL(page.url()).pathname).toBe("/");
      await expect(page.locator("main")).toHaveCount(1);
      await expect(page.locator("h1")).toHaveCount(1);
    }
  });

  test("industry scatter plot redraws after an explicit runtime resize", async ({ page }) => {
    test.skip(
      test.info().project.name !== "chrome-1440",
      "One stable-Chrome desktop execution is sufficient for the ResizeObserver redraw contract.",
    );

    const response = await page.goto("/explore/industries", { waitUntil: "networkidle" });
    expect(response?.ok()).toBeTruthy();
    const canvas = page
      .locator('figure[aria-label="RPS worker GenAI adoption (%) versus BTOS business AI use (%)"] .chart-canvas')
      .first();
    await expect(canvas).toBeVisible();
    const plot = canvas.locator("svg");
    await expect(plot).toHaveCount(1);

    const initialWidth = await plot.evaluate((element) => element.getBoundingClientRect().width);
    expect(initialWidth).toBeGreaterThan(800);

    await page.setViewportSize({ width: 720, height: 900 });
    await expect
      .poll(async () => plot.evaluate((element) => element.getBoundingClientRect().width))
      .toBeLessThan(initialWidth - 100);

    const resizedWidth = await plot.evaluate((element) => element.getBoundingClientRect().width);
    expect(resizedWidth).toBeGreaterThanOrEqual(280);
    expect(resizedWidth).toBeLessThan(initialWidth);
  });

  test("production not-found route returns an intelligible fail-closed 404 surface", async ({ page }) => {
    const consoleErrors: string[] = [];
    const pageErrors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });
    page.on("pageerror", (error) => pageErrors.push(error.message));

    const response = await page.goto("/__qa_not_a_release_route__", { waitUntil: "networkidle" });
    expect(response).not.toBeNull();
    expect(response?.status()).toBe(404);
    await expect(page.locator("body")).toContainText(/404|not found/i);
    await expect(page.locator("body")).not.toContainText("data/audit/private");
    expect(pageErrors).toEqual([]);

    const unexpectedConsoleErrors = consoleErrors.filter(
      (message) => message !== EXPECTED_404_CONSOLE_ERROR,
    );
    expect(unexpectedConsoleErrors).toEqual([]);
    expect(consoleErrors.length).toBeLessThanOrEqual(1);
  });

  test("industries: canonical BTOS-RPS triangulation is explicit and inspectable", async ({ page }) => {
    const response = await page.goto("/explore/industries", { waitUntil: "networkidle" });
    expect(response?.ok()).toBeTruthy();

    const section = page.locator('section[aria-labelledby="cross-source-triangulation"]');
    await expect(section).toBeVisible();
    await expect(
      section.getByRole("heading", {
        name: "Worker adoption and firm AI use show substantial sector concordance",
      }),
    ).toBeVisible();
    await expect(
      section.locator(".metric").filter({ hasText: "Primary sectors" }).locator("strong"),
    ).toHaveText("14");
    await expect(
      section.locator(".metric").filter({ hasText: "Spearman rank correlation" }).locator("strong"),
    ).toHaveText("0.704");
    await expect(
      section.locator(".metric").filter({ hasText: "Pearson correlation" }).locator("strong"),
    ).toHaveText("0.797");

    const boundary = section.locator("#btos-rps-measurement-boundary");
    await expect(boundary).toContainText("responding employer businesses");
    await expect(boundary).toContainText("employed adults");
    await expect(boundary).toContainText("distinct constructs");
    await expect(boundary).toContainText("Percentage-point gaps");
    await expect(boundary).toContainText("causal interpretation");

    await expect(
      section.locator('figure[aria-label="RPS worker GenAI adoption (%) versus BTOS business AI use (%)"]'),
    ).toBeVisible();

    const dataDetails = section.locator("details.data-details");
    await expect(dataDetails).toHaveCount(1);
    await dataDetails.locator("summary").click();
    await expect(dataDetails.locator("table")).toBeVisible();
    await expect(dataDetails.locator("tbody tr")).toHaveCount(14);

    const sensitivity = section.locator(".comparison-card").filter({ hasText: "Expanded sensitivity" });
    await expect(sensitivity).toContainText("17");
    await expect(sensitivity).toContainText("0.815");
    await expect(sensitivity).toContainText("0.850");
    await expect(sensitivity).toContainText("preregistered limited-comparability tier");
  });
});

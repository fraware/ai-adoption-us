import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const routes = [
  { slug: "home", path: "/" },
  { slug: "industries", path: "/explore/industries" },
  { slug: "occupations", path: "/explore/occupations" },
  { slug: "methodology", path: "/methodology" },
  { slug: "sources", path: "/sources" },
  { slug: "after-adoption", path: "/blog/after-adoption" },
] as const;

const primaryNavigation = [
  "/explore/industries",
  "/explore/occupations",
  "/blog/after-adoption",
  "/methodology",
  "/sources",
] as const;

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

      const tableCount = await page.locator("table").count();
      for (let index = 0; index < tableCount; index += 1) {
        const table = page.locator("table").nth(index);
        await expect(table).toBeVisible();
        await expect(table.locator("xpath=ancestor::*[contains(concat(' ', normalize-space(@class), ' '), ' table-wrap ')][1]")).toHaveCount(1);
      }

      // Test keyboard entry from the freshly loaded document. A pointer click before Tab
      // changes the browser's sequential-focus starting point and does not model a keyboard
      // user entering the page from browser chrome.
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

      expect(pageErrors, `Uncaught runtime errors on ${route.path}`).toEqual([]);
      expect(consoleErrors, `Console errors on ${route.path}`).toEqual([]);
    });
  }
});

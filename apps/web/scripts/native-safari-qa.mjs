import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const baseUrl = process.env.SAFARI_QA_BASE_URL ?? "http://127.0.0.1:3000";
const webdriverUrl = process.env.SAFARI_WEBDRIVER_URL ?? "http://127.0.0.1:4444";
const outputDir = path.resolve(process.argv[2] ?? "qa-results/native-safari");

const routes = [
  { slug: "home", pathname: "/" },
  { slug: "industries", pathname: "/explore/industries" },
  { slug: "occupations", pathname: "/explore/occupations" },
  { slug: "methodology", pathname: "/methodology" },
  { slug: "sources", pathname: "/sources" },
  { slug: "after-adoption", pathname: "/blog/after-adoption" },
];

const primaryNavigation = [
  "/explore/industries",
  "/explore/occupations",
  "/blog/after-adoption",
  "/methodology",
  "/sources",
];

function endpoint(pathname) {
  return new URL(pathname, `${webdriverUrl.replace(/\/$/, "")}/`).toString();
}

async function webdriverRequest(method, pathname, body) {
  const response = await fetch(endpoint(pathname), {
    method,
    headers: body === undefined ? undefined : { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(30_000),
  });

  const text = await response.text();
  let payload;
  try {
    payload = text ? JSON.parse(text) : {};
  } catch (error) {
    throw new Error(
      `SafariDriver returned non-JSON for ${method} ${pathname}: HTTP ${response.status}; ${text.slice(0, 500)}`,
      { cause: error },
    );
  }

  const protocolError = payload?.value?.error;
  if (!response.ok || protocolError) {
    const message = payload?.value?.message ?? text ?? "unknown SafariDriver error";
    throw new Error(
      `SafariDriver ${method} ${pathname} failed: HTTP ${response.status}; ${protocolError ?? "http_error"}: ${message}`,
    );
  }

  return payload?.value;
}

async function execute(sessionId, script, args = []) {
  return webdriverRequest("POST", `/session/${sessionId}/execute/sync`, { script, args });
}

async function waitForDocument(sessionId) {
  const deadline = Date.now() + 20_000;
  while (Date.now() < deadline) {
    const readyState = await execute(sessionId, "return document.readyState;");
    if (readyState === "complete") {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error("Safari document did not reach readyState=complete within 20 seconds");
}

async function captureScreenshot(sessionId, slug) {
  const base64 = await webdriverRequest("GET", `/session/${sessionId}/screenshot`);
  if (typeof base64 !== "string" || base64.length === 0) {
    throw new Error(`SafariDriver returned an invalid screenshot payload for ${slug}`);
  }
  await writeFile(path.join(outputDir, `${slug}.png`), Buffer.from(base64, "base64"));
}

await mkdir(outputDir, { recursive: true });

let sessionId;
const startedAt = new Date().toISOString();
const report = {
  startedAtUtc: startedAt,
  baseUrl,
  webdriverUrl,
  interpretation:
    "Native Safari desktop automation through the macOS-installed SafariDriver. This is not iOS Safari, physical-device, screen-reader, or manual-interaction evidence.",
  capabilities: null,
  routes: [],
};

try {
  const session = await webdriverRequest("POST", "/session", {
    capabilities: {
      alwaysMatch: {
        browserName: "safari",
      },
    },
  });

  sessionId = session?.sessionId;
  if (typeof sessionId !== "string" || sessionId.length === 0) {
    throw new Error(`SafariDriver did not return a W3C session id: ${JSON.stringify(session)}`);
  }
  report.capabilities = session.capabilities ?? null;

  try {
    await webdriverRequest("POST", `/session/${sessionId}/window/rect`, {
      width: 1440,
      height: 1000,
    });
  } catch (error) {
    report.windowRectWarning = error instanceof Error ? error.message : String(error);
  }

  for (const route of routes) {
    const url = new URL(route.pathname, baseUrl).toString();
    await webdriverRequest("POST", `/session/${sessionId}/url`, { url });
    await waitForDocument(sessionId);

    const assertions = await execute(
      sessionId,
      `
      const expectedPathname = arguments[0];
      const expectedNavigation = arguments[1];
      const visible = (element) => Boolean(element && element.getClientRects().length > 0);
      const visibleTables = Array.from(document.querySelectorAll("table")).filter(visible);
      const nav = document.querySelector('nav[aria-label="Primary navigation"]');
      const navPaths = nav
        ? Array.from(nav.querySelectorAll("a[href]")).map((anchor) => new URL(anchor.href, location.href).pathname)
        : [];
      return {
        pathname: location.pathname,
        expectedPathname,
        readyState: document.readyState,
        userAgent: navigator.userAgent,
        mainCount: document.querySelectorAll("main").length,
        h1Count: document.querySelectorAll("h1").length,
        primaryNavigationCount: document.querySelectorAll('nav[aria-label="Primary navigation"]').length,
        footerCount: document.querySelectorAll("footer.site-footer").length,
        missingNavigation: expectedNavigation.filter((pathname) => !navPaths.includes(pathname)),
        clientWidth: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
        visibleTableCount: visibleTables.length,
        visibleTablesOutsideWrappers: visibleTables.filter((table) => !table.closest(".table-wrap")).length,
      };
      `,
      [route.pathname, primaryNavigation],
    );

    const failures = [];
    if (assertions.pathname !== route.pathname) failures.push(`pathname=${assertions.pathname}`);
    if (assertions.readyState !== "complete") failures.push(`readyState=${assertions.readyState}`);
    if (!/Safari\//.test(assertions.userAgent) || !/Version\//.test(assertions.userAgent)) {
      failures.push(`unexpected Safari user agent: ${assertions.userAgent}`);
    }
    if (assertions.mainCount !== 1) failures.push(`mainCount=${assertions.mainCount}`);
    if (assertions.h1Count !== 1) failures.push(`h1Count=${assertions.h1Count}`);
    if (assertions.primaryNavigationCount !== 1) {
      failures.push(`primaryNavigationCount=${assertions.primaryNavigationCount}`);
    }
    if (assertions.footerCount !== 1) failures.push(`footerCount=${assertions.footerCount}`);
    if (assertions.missingNavigation.length > 0) {
      failures.push(`missingNavigation=${assertions.missingNavigation.join(",")}`);
    }
    if (assertions.scrollWidth > assertions.clientWidth + 1) {
      failures.push(`horizontalOverflow=${assertions.scrollWidth}-${assertions.clientWidth}`);
    }
    if (assertions.visibleTablesOutsideWrappers !== 0) {
      failures.push(`visibleTablesOutsideWrappers=${assertions.visibleTablesOutsideWrappers}`);
    }

    await captureScreenshot(sessionId, route.slug);

    const routeResult = {
      slug: route.slug,
      pathname: route.pathname,
      passed: failures.length === 0,
      failures,
      assertions,
    };
    report.routes.push(routeResult);

    if (failures.length > 0) {
      throw new Error(`Native Safari QA failed for ${route.pathname}: ${failures.join("; ")}`);
    }
  }

  report.passed = true;
} catch (error) {
  report.passed = false;
  report.error = error instanceof Error ? error.stack ?? error.message : String(error);
  throw error;
} finally {
  report.finishedAtUtc = new Date().toISOString();
  if (sessionId) {
    try {
      await webdriverRequest("DELETE", `/session/${sessionId}`);
    } catch (error) {
      report.sessionCleanupWarning = error instanceof Error ? error.message : String(error);
    }
  }
  await writeFile(path.join(outputDir, "native-safari-report.json"), `${JSON.stringify(report, null, 2)}\n`);
}

export function configuredSiteBaseUrl(): string | null {
  const raw = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  if (!raw) return null;

  const url = new URL(raw);
  if (url.protocol !== "https:" && url.protocol !== "http:") {
    throw new Error("NEXT_PUBLIC_SITE_URL must use http or https");
  }
  if (url.search || url.hash) {
    throw new Error("NEXT_PUBLIC_SITE_URL must not include a query or fragment");
  }

  const normalizedPath = url.pathname.replace(/\/+$/, "");
  return `${url.origin}${normalizedPath}`;
}

export function absoluteSiteUrl(path = "/"): string | null {
  const baseUrl = configuredSiteBaseUrl();
  if (!baseUrl) return null;

  if (path === "/") return `${baseUrl}/`;
  return `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

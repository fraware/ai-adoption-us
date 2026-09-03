import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const RELEASE_ID_RE = /^[a-z0-9][a-z0-9._-]{0,127}$/;
const SHA256_RE = /^[0-9a-f]{64}$/;

const PROJECT_ROOT = path.resolve(process.cwd(), "..", "..");
const REGISTRY_PATH = path.join(
  PROJECT_ROOT,
  "data",
  "registry",
  "observatory_release_registry.json",
);
const RELEASES_ROOT = path.join(PROJECT_ROOT, "data", "releases");

type ReleaseRegistryRow = {
  release_id: string;
  manifest_sha256: string;
};

type ReleaseRegistry = {
  schema_version: number;
  current_release_id: string | null;
  current_release_manifest_sha256: string | null;
  releases: ReleaseRegistryRow[];
  status: string;
};

type ReleaseArtifact = {
  artifact_id: string;
  path: string;
  sha256: string;
  size_bytes: number;
};

type ReleaseSource = {
  source_id: string;
  source_vintage_id: string;
  retrieved_at: string;
};

export type PromotedReleaseManifest = {
  schema_version: number;
  release_id: string;
  release_status: string;
  artifacts: ReleaseArtifact[];
  sources: ReleaseSource[];
};

export type CurrentPromotedRelease = {
  root: string;
  manifest: PromotedReleaseManifest;
  manifestSha256: string;
};

function assertSha256(value: unknown, context: string): asserts value is string {
  if (typeof value !== "string" || !SHA256_RE.test(value)) {
    throw new Error(`${context} must be a lowercase SHA-256 digest`);
  }
}

function assertReleaseId(value: unknown, context: string): asserts value is string {
  if (typeof value !== "string" || !RELEASE_ID_RE.test(value)) {
    throw new Error(`${context} is not a safe release identifier`);
  }
}

async function sha256File(file: string): Promise<string> {
  const bytes = await fs.readFile(file);
  return createHash("sha256").update(bytes).digest("hex");
}

async function readJson<T>(file: string): Promise<T> {
  return JSON.parse(await fs.readFile(file, "utf8")) as T;
}

function resolveArtifactPath(releaseRoot: string, relative: string): string {
  if (
    path.posix.isAbsolute(relative) ||
    relative.includes("\\") ||
    relative.split("/").includes("..") ||
    !relative.startsWith("artifacts/")
  ) {
    throw new Error(`Unsafe promoted release artifact path: ${relative}`);
  }
  const resolvedRoot = path.resolve(releaseRoot);
  const resolved = path.resolve(releaseRoot, ...relative.split("/"));
  if (!resolved.startsWith(`${resolvedRoot}${path.sep}`)) {
    throw new Error(`Promoted release artifact escapes its release root: ${relative}`);
  }
  return resolved;
}

export async function loadCurrentPromotedRelease(): Promise<CurrentPromotedRelease | null> {
  const registry = await readJson<ReleaseRegistry>(REGISTRY_PATH);
  if (registry.schema_version !== 1 || !Array.isArray(registry.releases)) {
    throw new Error("Observatory release registry schema is invalid");
  }

  const releaseId = registry.current_release_id;
  const manifestSha = registry.current_release_manifest_sha256;
  if (releaseId === null) {
    if (manifestSha !== null) {
      throw new Error("Release registry has a manifest checksum without a current release");
    }
    return null;
  }

  assertReleaseId(releaseId, "current_release_id");
  assertSha256(manifestSha, "current_release_manifest_sha256");
  if (registry.status !== "CURRENT_RELEASE_PROMOTED") {
    throw new Error(`Current release exists with unexpected registry status: ${registry.status}`);
  }

  const registered = registry.releases.filter((row) => row.release_id === releaseId);
  if (registered.length !== 1 || registered[0].manifest_sha256 !== manifestSha) {
    throw new Error("Current release pointer does not match exactly one immutable registry row");
  }

  const releaseRoot = path.join(RELEASES_ROOT, releaseId);
  const manifestPath = path.join(releaseRoot, "release_manifest.json");
  const observedManifestSha = await sha256File(manifestPath);
  if (observedManifestSha !== manifestSha) {
    throw new Error("Promoted release manifest checksum does not match the registry pointer");
  }

  const manifest = await readJson<PromotedReleaseManifest>(manifestPath);
  if (manifest.schema_version !== 1 || manifest.release_id !== releaseId) {
    throw new Error("Promoted release manifest identity does not match the registry pointer");
  }
  if (manifest.release_status !== "PROMOTED_AFTER_EXPLICIT_REVIEW") {
    throw new Error(`Unexpected promoted release status: ${manifest.release_status}`);
  }
  if (!Array.isArray(manifest.artifacts) || !Array.isArray(manifest.sources)) {
    throw new Error("Promoted release manifest is missing artifacts or sources");
  }

  return { root: releaseRoot, manifest, manifestSha256: manifestSha };
}

export async function readCurrentReleaseJsonArtifact<T>(
  artifactId: string,
): Promise<{ value: T; release: CurrentPromotedRelease } | null> {
  const release = await loadCurrentPromotedRelease();
  if (release === null) return null;

  const matches = release.manifest.artifacts.filter((row) => row.artifact_id === artifactId);
  if (matches.length !== 1) {
    throw new Error(`Promoted release must contain exactly one ${artifactId} artifact`);
  }
  const artifact = matches[0];
  assertSha256(artifact.sha256, `${artifactId}.sha256`);
  if (!Number.isSafeInteger(artifact.size_bytes) || artifact.size_bytes < 0) {
    throw new Error(`${artifactId}.size_bytes is invalid`);
  }

  const artifactPath = resolveArtifactPath(release.root, artifact.path);
  const stat = await fs.stat(artifactPath);
  if (!stat.isFile() || stat.size !== artifact.size_bytes) {
    throw new Error(`Promoted release artifact size mismatch: ${artifactId}`);
  }
  const observedSha = await sha256File(artifactPath);
  if (observedSha !== artifact.sha256) {
    throw new Error(`Promoted release artifact checksum mismatch: ${artifactId}`);
  }

  return {
    value: await readJson<T>(artifactPath),
    release,
  };
}

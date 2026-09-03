import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const RELEASE_ID_RE = /^[a-z0-9][a-z0-9._-]{0,127}$/;
const SHA256_RE = /^[0-9a-f]{64}$/;

const DATA_ROOT = path.join(process.cwd(), "..", "..", "data");
const REGISTRY_PATH = path.join(DATA_ROOT, "registry", "observatory_release_registry.json");
const RELEASES_ROOT = path.join(DATA_ROOT, "releases");

type ReleaseRegistryEntry = {
  release_id: string;
  manifest_sha256: string;
};

type ReleaseRegistry = {
  schema_version: number;
  current_release_id: string | null;
  current_release_manifest_sha256: string | null;
  releases: ReleaseRegistryEntry[];
};

type ReleaseArtifact = {
  artifact_id: string;
  path: string;
  sha256: string;
  size_bytes: number;
};

type PublicReleaseManifest = {
  release_id: string;
  release_status?: string;
  artifacts: ReleaseArtifact[];
};

export type ResolvedReleaseArtifact = {
  releaseId: string;
  artifactId: string;
  filePath: string;
  sha256: string;
  sizeBytes: number;
};

function assertSha256(value: unknown, context: string): asserts value is string {
  if (typeof value !== "string" || !SHA256_RE.test(value)) {
    throw new Error(`${context} must be a lowercase SHA-256 digest`);
  }
}

function assertSafeReleaseId(value: unknown, context: string): asserts value is string {
  if (typeof value !== "string" || !RELEASE_ID_RE.test(value)) {
    throw new Error(`${context} is not a safe release identifier`);
  }
}

function safeArtifactPath(releaseDir: string, relative: unknown): string {
  if (
    typeof relative !== "string" ||
    relative.includes("\\") ||
    path.posix.isAbsolute(relative)
  ) {
    throw new Error("Release artifact path is invalid");
  }
  const parts = relative.split("/");
  if (parts.length < 2 || parts[0] !== "artifacts" || parts.some((part) => !part || part === "..")) {
    throw new Error(`Release artifact path escapes the public artifact namespace: ${relative}`);
  }
  const resolvedRoot = path.resolve(releaseDir);
  const resolved = path.resolve(releaseDir, ...parts);
  if (!resolved.startsWith(`${resolvedRoot}${path.sep}`)) {
    throw new Error(`Release artifact path escapes release directory: ${relative}`);
  }
  return resolved;
}

async function sha256Bytes(value: Buffer): Promise<string> {
  return createHash("sha256").update(value).digest("hex");
}

async function loadCurrentReleaseManifest(): Promise<{
  releaseId: string;
  releaseDir: string;
  manifest: PublicReleaseManifest;
} | null> {
  const registry = JSON.parse(await fs.readFile(REGISTRY_PATH, "utf8")) as ReleaseRegistry;
  if (registry.schema_version !== 1 || !Array.isArray(registry.releases)) {
    throw new Error("Observatory release registry has an unsupported structure");
  }

  const releaseId = registry.current_release_id;
  if (releaseId === null) {
    if (registry.current_release_manifest_sha256 !== null) {
      throw new Error("Release registry has a manifest digest without a current release");
    }
    return null;
  }
  assertSafeReleaseId(releaseId, "current_release_id");
  assertSha256(
    registry.current_release_manifest_sha256,
    "current_release_manifest_sha256",
  );

  const matchingEntries = registry.releases.filter((row) => row.release_id === releaseId);
  if (matchingEntries.length !== 1) {
    throw new Error(`Release registry must contain exactly one entry for ${releaseId}`);
  }
  assertSha256(matchingEntries[0].manifest_sha256, "registered release manifest_sha256");
  if (matchingEntries[0].manifest_sha256 !== registry.current_release_manifest_sha256) {
    throw new Error("Current release registry hashes disagree");
  }

  const releaseDir = path.join(RELEASES_ROOT, releaseId);
  const manifestPath = path.join(releaseDir, "release_manifest.json");
  const manifestBytes = await fs.readFile(manifestPath);
  const manifestSha = await sha256Bytes(manifestBytes);
  if (manifestSha !== registry.current_release_manifest_sha256) {
    throw new Error("Current Observatory release manifest checksum mismatch");
  }
  const manifest = JSON.parse(manifestBytes.toString("utf8")) as PublicReleaseManifest;
  if (manifest.release_id !== releaseId) {
    throw new Error("Current Observatory release ID does not match its manifest");
  }
  if (manifest.release_status !== "PROMOTED_AFTER_EXPLICIT_REVIEW") {
    throw new Error("Current Observatory release is not explicitly promoted");
  }
  if (!Array.isArray(manifest.artifacts)) {
    throw new Error("Current Observatory release manifest has no artifact inventory");
  }
  return { releaseId, releaseDir, manifest };
}

export async function resolveCurrentReleaseArtifact(
  artifactId: string,
): Promise<ResolvedReleaseArtifact | null> {
  const current = await loadCurrentReleaseManifest();
  if (!current) return null;

  const matches = current.manifest.artifacts.filter((row) => row.artifact_id === artifactId);
  if (matches.length !== 1) {
    throw new Error(
      `Promoted release ${current.releaseId} must contain exactly one artifact ${artifactId}`,
    );
  }
  const artifact = matches[0];
  assertSha256(artifact.sha256, `${artifactId}.sha256`);
  if (
    !Number.isSafeInteger(artifact.size_bytes) ||
    artifact.size_bytes < 0
  ) {
    throw new Error(`${artifactId}.size_bytes is invalid`);
  }
  const filePath = safeArtifactPath(current.releaseDir, artifact.path);
  const bytes = await fs.readFile(filePath);
  if (bytes.byteLength !== artifact.size_bytes) {
    throw new Error(`Promoted artifact size mismatch: ${artifactId}`);
  }
  if ((await sha256Bytes(bytes)) !== artifact.sha256) {
    throw new Error(`Promoted artifact checksum mismatch: ${artifactId}`);
  }
  return {
    releaseId: current.releaseId,
    artifactId,
    filePath,
    sha256: artifact.sha256,
    sizeBytes: artifact.size_bytes,
  };
}

export async function readCurrentReleaseJsonArtifact<T>(
  artifactId: string,
): Promise<{ releaseId: string; value: T } | null> {
  const resolved = await resolveCurrentReleaseArtifact(artifactId);
  if (!resolved) return null;
  const value = JSON.parse(await fs.readFile(resolved.filePath, "utf8")) as T;
  return { releaseId: resolved.releaseId, value };
}

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB="$ROOT/apps/web"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cat > "$TMP/stubs.d.ts" <<'STUBS'
declare module "next" { export type Metadata = Record<string, unknown>; }
declare module "next/link" { const Link: (props: Record<string, unknown>) => unknown; export default Link; }
declare namespace React { export type ReactNode = unknown; }
declare module "react" {
  export type ReactNode = unknown;
  export function useEffect(effect: () => void | (() => void), deps?: unknown[]): void;
  export function useRef<T>(initial: T | null): { current: T | null };
}
declare module "react/jsx-runtime" {
  export const Fragment: unknown;
  export function jsx(type: unknown, props: unknown, key?: unknown): unknown;
  export function jsxs(type: unknown, props: unknown, key?: unknown): unknown;
}
declare module "@observablehq/plot" {
  export type PlotOptions = Record<string, unknown>;
  export function plot(options: PlotOptions): { remove(): void } & Node;
  export function dot(data: unknown, options?: Record<string, unknown>): unknown;
  export function line(data: unknown, options?: Record<string, unknown>): unknown;
  export function lineY(data: unknown, options?: Record<string, unknown>): unknown;
  export function text(data: unknown, options?: Record<string, unknown>): unknown;
  export function ruleY(data: unknown, options?: Record<string, unknown>): unknown;
}
declare module "node:fs/promises" {
  const fs: { readFile(path: string, encoding: string): Promise<string> };
  export default fs;
}
declare module "node:path" {
  const path: { join(...parts: string[]): string };
  export default path;
}
declare const process: { cwd(): string; env: Record<string, string | undefined> };
declare namespace JSX { interface IntrinsicElements { [elemName: string]: Record<string, unknown>; } }
STUBS

cat > "$TMP/tsconfig.json" <<EOF2
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "strict": true,
    "noEmit": true,
    "skipLibCheck": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "esModuleInterop": true
  },
  "files": ["$TMP/stubs.d.ts"],
  "include": ["$WEB/**/*.ts", "$WEB/**/*.tsx"]
}
EOF2

if ! command -v tsc >/dev/null 2>&1; then
  echo "tsc is not installed in this runtime; structural TypeScript check cannot run." >&2
  exit 2
fi

tsc -p "$TMP/tsconfig.json"

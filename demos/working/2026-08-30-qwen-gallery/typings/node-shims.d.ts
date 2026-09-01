/**
 * Minimal ambient types for the Node globals used by the Playwright specs and
 * the validation harness. `@types/node` is not installed in this offline
 * workspace, so the handful of surfaces actually touched are declared here.
 * Types only: nothing here is bundled into the browser app.
 */

declare module "node:fs" {
  export function readFileSync(file: string, encoding?: string): string;
  export function existsSync(file: string): boolean;
  export function writeFileSync(file: string, data: string): void;
}

declare module "node:path" {
  export function resolve(...parts: string[]): string;
  export function join(...parts: string[]): string;
  export function dirname(from: string): string;
  export function basename(from: string): string;
  const pathModule: {
    resolve: typeof resolve;
    join: typeof join;
    dirname: typeof dirname;
    basename: typeof basename;
  };
  export default pathModule;
}

interface NodeProcess {
  readonly argv: string[];
  readonly env: Record<string, string | undefined>;
  cwd(): string;
  exit(code?: number): never;
  stdout?: { write(chunk: string): void };
  stderr?: { write(chunk: string): void };
}

declare var process: NodeProcess;
declare var __dirname: string;
declare var __filename: string;

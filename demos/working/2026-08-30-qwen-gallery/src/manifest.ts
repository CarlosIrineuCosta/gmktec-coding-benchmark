import type { RawManifestImage } from "virtual:gallery-manifest";
import { DISPLAY_META, captionFor, licenseLabel, titleFor } from "./display-meta";

export type Orientation = "portrait" | "landscape" | "square";

/** Normalised, render-ready view model for one corpus image. */
export interface GalleryImage {
  id: string;
  index: number;
  title: string;
  /** Short sentence shown under the thumbnail and in the lightbox. */
  caption: string;
  /** Meaningful alternative text (never empty). */
  alt: string;
  src: string;
  width: number;
  height: number;
  /** width / height, guarded against zero. */
  ratio: number;
  ratioCss: string;
  orientation: Orientation;
  creator: string;
  license: string;
  licenseLabel: string;
  filename: string;
  sha256: string;
  sourcePage: string;
  year?: string;
  medium?: string;
  repository?: string;
}

const BASE_URL = import.meta.env.BASE_URL || "/";

function joinImage(filename: string): string {
  const base = BASE_URL.endsWith("/") ? BASE_URL : `${BASE_URL}/`;
  return `${base}images/${encodeURIComponent(filename)}`;
}

function orientationOf(width: number, height: number): Orientation {
  if (!width || !height) return "landscape";
  const ratio = width / height;
  if (Math.abs(ratio - 1) <= 0.02) return "square";
  return ratio > 1 ? "landscape" : "portrait";
}

function positiveInt(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) && value > 0 ? value : fallback;
}

function text(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

/**
 * Turns manifest rows into view models. Rows without a usable id or filename
 * are skipped (they could never render); anything else is repaired rather than
 * dropped, so one incomplete row cannot blank the gallery.
 */
export function normalizeManifest(
  rows: readonly Partial<RawManifestImage>[],
): GalleryImage[] {
  const seen = new Set<string>();
  const images: GalleryImage[] = [];

  for (const row of rows) {
    const filename = text(row.local_filename);
    const id = text(row.id) || filename;
    if (!id || !filename || seen.has(id)) continue;
    seen.add(id);

    const width = positiveInt(row.width, 960);
    const height = positiveInt(row.height, 640);
    const title = titleFor(id);
    const meta = DISPLAY_META[id];
    const creator = text(row.creator) || "Unknown creator";
    const license = text(row.license) || "unspecified";

    images.push({
      id,
      index: images.length,
      title,
      caption: captionFor(id),
      alt: `${title} — ${creator}`,
      src: joinImage(filename),
      width,
      height,
      ratio: width / height,
      // Declared up front so each box has its final shape before the bytes
      // arrive, which keeps the intrinsic aspect ratio stable while loading.
      ratioCss: `${width} / ${height}`,
      orientation: orientationOf(width, height),
      creator,
      license,
      licenseLabel: licenseLabel(license),
      filename,
      sha256: text(row.sha256),
      sourcePage: text(row.source_page),
      year: meta?.year,
      medium: meta?.medium,
      repository: meta?.repository,
    });
  }

  return images;
}

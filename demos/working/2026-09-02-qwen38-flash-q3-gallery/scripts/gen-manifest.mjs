/**
 * Generates `src/generated/manifest.ts` from `public/images.json`.
 *
 * The manifest is bundled into the application at build time so the running
 * gallery never needs a network request for metadata or images. This script
 * is also the acquisition audit: it re-hashes every local asset and re-reads
 * each JPEG header so the recorded sha256/width/height cannot silently drift
 * away from the bytes actually shipped in `public/images/`.
 */

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MANIFEST_PATH = path.join(ROOT, "public", "images.json");
const IMAGES_DIR = path.join(ROOT, "public", "images");
const OUTPUT_PATH = path.join(ROOT, "src", "generated", "manifest.ts");

/** Fields every record must carry, supplied or acquired. */
const BASE_FIELDS = [
  "id",
  "local_filename",
  "title",
  "category",
  "source_page",
  "sha256",
  "width",
  "height"
];

/** Full provenance schema, enforced on records acquired by this task only. */
const REQUIRED_FIELDS = [
  "id",
  "local_filename",
  "title",
  "creator",
  "date",
  "institution",
  "rights",
  "source_page",
  "rights_page",
  "download_url",
  "sha256",
  "width",
  "height",
  "category"
];

/** Institutions whose records were acquired during this task's download pass. */
const ACQUIRED_INSTITUTIONS = new Set(["The Metropolitan Museum of Art", "Library of Congress"]);

/** Rights values this project is allowed to publish under. */
const ACCEPTED_RIGHTS = new Set(["CC0", "public-domain", "no-known-copyright-restrictions"]);

const errors = [];
const warnings = [];

/** Minimal JPEG SOF reader: avoids pulling an image dependency into the build. */
function jpegSize(data) {
  if (!data.subarray(0, 2).equals(Buffer.from([0xff, 0xd8]))) return null;
  let offset = 2;
  while (offset + 9 <= data.length) {
    if (data[offset] !== 0xff) {
      offset += 1;
      continue;
    }
    const marker = data[offset + 1];
    offset += 2;
    if (marker === 0xd8 || marker === 0xd9 || (marker >= 0xd0 && marker <= 0xd7)) continue;
    if (offset + 2 > data.length) break;
    const length = data.readUInt16BE(offset);
    if (length < 2 || offset + length > data.length) break;
    const frameMarkers = new Set([
      0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf
    ]);
    if (frameMarkers.has(marker)) {
      return { height: data.readUInt16BE(offset + 3), width: data.readUInt16BE(offset + 5) };
    }
    offset += length;
  }
  return null;
}

const records = JSON.parse(await readFile(MANIFEST_PATH, "utf8"));

if (!Array.isArray(records)) throw new Error("public/images.json must contain an array");

const seenIds = new Set();
const seenFiles = new Set();
const categoryCounts = new Map();
let totalBytes = 0;

for (const [index, record] of records.entries()) {
  const label = record.id || `record #${index}`;
  const acquired = ACQUIRED_INSTITUTIONS.has(record.institution);

  for (const field of acquired ? REQUIRED_FIELDS : BASE_FIELDS) {
    if (!(field in record)) errors.push(`${label}: missing required field "${field}"`);
  }

  if (seenIds.has(record.id)) errors.push(`${label}: duplicate id`);
  seenIds.add(record.id);

  if (seenFiles.has(record.local_filename)) errors.push(`${label}: duplicate local_filename`);
  seenFiles.add(record.local_filename);

  if (record.institution === "The Metropolitan Museum of Art" || record.institution === "Library of Congress") {
    if (!ACCEPTED_RIGHTS.has(record.rights)) errors.push(`${label}: unexpected rights value "${record.rights}"`);    for (const field of ["source_page", "rights_page", "download_url"]) {
      const value = record[field];
      if (typeof value !== "string" || !/^https:\/\//.test(value)) {
        errors.push(`${label}: ${field} must be an https URL for acquired records`);
      }
    }
  }

  if (typeof record.category !== "string" || record.category.trim() === "") {
    errors.push(`${label}: category must be a non-empty string`);
  } else {
    categoryCounts.set(record.category, (categoryCounts.get(record.category) ?? 0) + 1);
  }

  const filePath = path.join(IMAGES_DIR, record.local_filename ?? "");
  let data;
  try {
    data = await readFile(filePath);
  } catch {
    errors.push(`${label}: public/images/${record.local_filename} is not readable`);
    continue;
  }

  totalBytes += data.length;
  const digest = createHash("sha256").update(data).digest("hex");
  if (digest !== record.sha256) {
    const message = `${label}: sha256 mismatch (recorded ${record.sha256}, file ${digest})`;
    if (acquired) errors.push(message);
    else warnings.push(`${message} — supplied record left untouched`);
  }

  const size = jpegSize(data);
  if (!size) {
    warnings.push(`${label}: not a JPEG, dimensions taken from the record`);
  } else if (size.width !== record.width || size.height !== record.height) {
    errors.push(
      `${label}: dimensions mismatch (recorded ${record.width}x${record.height}, file ${size.width}x${size.height})`
    );
  }

  if (!record.title || typeof record.title !== "string") errors.push(`${label}: title is required`);
}

const nonEmptyCategories = [...categoryCounts.entries()].filter(([, count]) => count > 0);

if (records.length !== 24) errors.push(`expected 24 records, found ${records.length}`);
if (nonEmptyCategories.length < 3) {
  errors.push(`expected at least three non-empty categories, found ${nonEmptyCategories.length}`);
}
if (!records.every((record) => /^images\/|^[a-z0-9][a-z0-9-]*\.jpg$/.test(record.local_filename))) {
  errors.push("every local_filename must be a lowercase .jpg filename");
}

if (errors.length > 0) {
  console.error(`manifest validation failed:\n- ${errors.join("\n- ")}`);
  process.exit(1);
}

const banner = `/**
 * AUTO-GENERATED by scripts/gen-manifest.mjs — do not edit by hand.
 * Source of truth: public/images.json (validated against public/images/).
 * ${records.length} local works, ${(totalBytes / (1024 * 1024)).toFixed(1)} MB of JPEG data, all local.
 */

import type { ImageRecord } from "../types";

export const images: ImageRecord[] = `;

const body = JSON.stringify(records, null, 2).replace(/<\/script>/gim, "<\\/script>");
await mkdir(path.dirname(OUTPUT_PATH), { recursive: true });
await writeFile(OUTPUT_PATH, `${banner}${body};\n`, "utf8");

const summary = nonEmptyCategories
  .map(([category, count]) => `${category}: ${count}`)
  .join(", ");
console.log(
  `manifest ok — ${records.length} local works (${(totalBytes / (1024 * 1024)).toFixed(1)} MB) across ${
    nonEmptyCategories.length
  } categories (${summary})`
);
for (const warning of warnings) console.warn(`warning: ${warning}`);

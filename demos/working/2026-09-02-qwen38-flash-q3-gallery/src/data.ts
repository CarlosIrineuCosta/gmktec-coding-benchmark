import { images } from "./generated/manifest";
import type { CategoryOption, ImageRecord, WorkView } from "./types";

/** Label of the "show everything" control. */
export const ALL = "All";

/** Deterministic category ordering for the filter bar. */
const CATEGORY_ORDER = [
  "Portraits",
  "Landscapes",
  "Still Life",
  "Mythology & Allegory",
  "Prints & Drawings"
];

/** Leading phrase of the alternative text, per category. */
const ALTERNATIVE_LEADS: Record<string, string> = {
  Portraits: "Portrait",
  Landscapes: "Landscape",
  "Still Life": "Still life",
  "Mythology & Allegory": "Allegorical scene",
  "Prints & Drawings": "Print"
};

const RIGHTS_LONG: Record<string, string> = {
  CC0: "CC0 1.0 Universal — The Met Open Access",
  "public-domain": "Public domain",
  "no-known-copyright-restrictions": "No known copyright restrictions"
};

const RIGHTS_SHORT: Record<string, string> = {
  CC0: "CC0",
  "public-domain": "Public domain",
  "no-known-copyright-restrictions": "No known restrictions"
};

const base = import.meta.env.BASE_URL ?? "/";

/** Local asset URL; the gallery has no remote image origin at runtime. */
export function imageSrc(filename: string): string {
  return `${base}images/${filename}`;
}

export function rightsLong(record: ImageRecord): string {
  return RIGHTS_LONG[record.rights] ?? record.rights;
}

export function rightsShort(record: ImageRecord): string {
  return RIGHTS_SHORT[record.rights] ?? record.rights;
}

function attributionFor(record: ImageRecord): string {
  const creator = record.creator?.trim();
  const date = record.date?.trim();
  if (creator && date) return `${creator}, ${date}`;
  if (creator) return creator;
  if (date) return `${date}, artist unknown`;
  return "Artist and date unrecorded";
}

function altFor(record: ImageRecord): string {
  const lead = ALTERNATIVE_LEADS[record.category] ?? "Artwork";
  const creator = record.creator ? ` by ${record.creator}` : "";
  const date = record.date ? `, ${record.date}` : "";
  return `${lead}, "${record.title}"${creator}${date}. Reproduction from ${record.institution} (${rightsShort(
    record
  )}).`;
}

/** Works in manifest order: the twelve supplied masters, then The Met additions. */
export function buildWorks(): WorkView[] {
  return images.map((record) => ({
    record,
    src: imageSrc(record.local_filename),
    alt: altFor(record),
    attribution: attributionFor(record),
    rightsShort: rightsShort(record),
    rightsLong: rightsLong(record),
    ratio: record.width / record.height
  }));
}

/** Filter options, `All` first, then every category that actually has works. */
export function categoryOptions(works: WorkView[]): CategoryOption[] {
  const counts = new Map<string, number>();
  for (const work of works) {
    counts.set(work.record.category, (counts.get(work.record.category) ?? 0) + 1);
  }
  const ordered = [...counts.keys()].sort((a, b) => {
    const aIndex = CATEGORY_ORDER.indexOf(a);
    const bIndex = CATEGORY_ORDER.indexOf(b);
    if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
    if (aIndex !== -1) return -1;
    if (bIndex !== -1) return 1;
    return a.localeCompare(b);
  });
  return [{ label: ALL, count: works.length }, ...ordered.map((label) => ({ label, count: counts.get(label)! }))];
}

export function worksInCategory(works: WorkView[], category: string): WorkView[] {
  return category === ALL ? works : works.filter((work) => work.record.category === category);
}

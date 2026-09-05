export type RightsValue = "CC0" | "public-domain" | "no-known-copyright-restrictions" | string;

/** One published work. Every field here comes from `public/images.json`. */
export interface ImageRecord {
  id: string;
  local_filename: string;
  title: string;
  creator: string | null;
  date?: string | null;
  category: string;
  institution: string;
  rights: RightsValue;
  license?: string;
  source_page: string;
  rights_page?: string;
  download_url?: string;
  sha256: string;
  width: number;
  height: number;
}

/** A record plus everything the UI needs to render it accessibly. */
export interface WorkView {
  record: ImageRecord;
  /** Root-relative URL of the local JPEG (never a remote host). */
  src: string;
  /** Descriptive alternative text for the thumbnail and the lightbox image. */
  alt: string;
  /** "Creator, date" or a fallback when the source has no attribution. */
  attribution: string;
  /** Short rights label for the card, e.g. "CC0". */
  rightsShort: string;
  /** Full rights statement for the lightbox. */
  rightsLong: string;
  /** Aspect ratio (width / height) used to reserve layout space. */
  ratio: number;
}

export interface CategoryOption {
  label: string;
  count: number;
}

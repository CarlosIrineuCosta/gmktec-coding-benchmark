/**
 * Curated display metadata, keyed by manifest `id`.
 *
 * The manifest carries provenance (creator, licence, pixels, source page) but
 * no human-readable title, so titles/captions live here. `titleFor()` and
 * `captionFor()` degrade gracefully for any id that is not curated, so a
 * manifest that grows never renders an empty caption.
 */

interface DisplayMeta {
  title: string;
  year?: string;
  medium?: string;
  repository?: string;
  caption: string;
}

export const DISPLAY_META: Record<string, DisplayMeta> = {
  "great-wave": {
    title: "The Great Wave off Kanagawa",
    year: "c. 1831",
    medium: "Colour woodblock print",
    repository: "Metropolitan Museum of Art",
    caption:
      "A crested wave hangs over boats in Kanagawa's bay, with Mount Fuji small and serene behind it.",
  },
  "starry-night": {
    title: "The Starry Night",
    year: "1889",
    medium: "Oil on canvas",
    repository: "Museum of Modern Art, New York",
    caption:
      "Swirling night air and an incandescent moon turn the view from Saint-Rémy into pure movement.",
  },
  "mona-lisa": {
    title: "Mona Lisa",
    year: "c. 1503–1519",
    medium: "Oil on poplar panel",
    repository: "Musée du Louvre",
    caption:
      "Lisa Gherardini's half-length portrait, famously softened with sfumato against a hazy landscape.",
  },
  "pearl-earring": {
    title: "Girl with a Pearl Earring",
    year: "c. 1665",
    medium: "Oil on canvas",
    repository: "Mauritshuis, The Hague",
    caption:
      "A tronie in a turban and a single drop of light: the girl turns from shadow toward the viewer.",
  },
  wanderer: {
    title: "Wanderer above the Sea of Fog",
    year: "c. 1818",
    medium: "Oil on canvas",
    repository: "Hamburger Kunsthalle",
    caption:
      "A man stands with his back to us on a rocky ledge, surveying a landscape dissolving into mist.",
  },
  liberty: {
    title: "Liberty Leading the People",
    year: "1830",
    medium: "Oil on canvas",
    repository: "Musée du Louvre",
    caption:
      "Marianne leads a barricade crowd over the rubble of the July Revolution, tricolour raised high.",
  },
  "hay-wain": {
    title: "The Hay Wain",
    year: "1821",
    medium: "Oil on canvas",
    repository: "National Gallery, London",
    caption:
      "A cart crosses the Stour at Flatford, the Suffolk sky doing most of Constable's work.",
  },
  temeraire: {
    title: "The Fighting Temeraire",
    year: "1839",
    medium: "Oil on canvas",
    repository: "National Gallery, London",
    caption:
      "A battered warship is towed to break-up by a small steam tug, sunset bleeding behind the masts.",
  },
  "lady-shalott": {
    title: "The Lady of Shalott",
    year: "1888",
    medium: "Oil on canvas",
    repository: "Tate, London",
    caption:
      "Under an autumn sky, the cursed lady leaves her tower and drifts toward Camelot.",
  },
  "grande-jatte": {
    title: "A Sunday Afternoon on the Island of La Grande Jatte",
    year: "1884–1886",
    medium: "Oil on canvas",
    repository: "Art Institute of Chicago",
    caption:
      "Seurat's pointillist promenade: Parisians strolling and resting on the Seine, built from dots of colour.",
  },
  "birth-venus": {
    title: "The Birth of Venus",
    year: "c. 1485",
    medium: "Tempera on canvas",
    repository: "Uffizi Gallery, Florence",
    caption:
      "Venus arrives on a shell at the shore, blown ashore by the winds and handed a flowered cloak.",
  },
  "garden-delights": {
    title: "The Garden of Earthly Delights",
    year: "c. 1490–1510",
    medium: "Oil on panels (triptych)",
    repository: "Museo del Prado, Madrid",
    caption:
      "Bosch's central panel teems with nudes, birds and impossible fruit in an earthly paradise.",
  },
};

const LICENSE_LABELS: Record<string, string> = {
  "public-domain": "Public domain",
  cc0: "CC0 1.0 Universal",
  "cc-by": "CC BY",
  "cc-by-sa": "CC BY-SA",
};

export function licenseLabel(license: string): string {
  const key = license.trim().toLowerCase();
  return LICENSE_LABELS[key] ?? license.replace(/-/g, " ");
}

/** "great-wave" -> "Great Wave"; used only when no curated title exists. */
export function titleFromId(id: string): string {
  return id
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function titleFor(id: string): string {
  return DISPLAY_META[id]?.title?.trim() || titleFromId(id);
}

export function captionFor(id: string): string {
  return DISPLAY_META[id]?.caption?.trim() || `Artwork ${titleFor(id)}.`;
}

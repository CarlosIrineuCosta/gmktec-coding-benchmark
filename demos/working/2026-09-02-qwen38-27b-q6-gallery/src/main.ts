import imagesData from "../public/images.json";
import "./styles.css";

/**
 * Open Access Gallery
 *
 * A local-only gallery of public-domain artworks. All image files live in
 * `public/images/` and every record is described in `public/images.json`
 * (bundled at build time, so the page never makes a remote request).
 */

interface GalleryImage {
  id: string;
  local_filename: string;
  title: string;
  creator?: string | null;
  date?: string | null;
  institution: string;
  rights: string;
  license?: string;
  source_page: string;
  rights_page?: string;
  download_url?: string;
  sha256: string;
  width: number;
  height: number;
  category: string;
}

const images: GalleryImage[] = imagesData as unknown as GalleryImage[];

const ALL_FILTER = "All";
const PREFERRED_CATEGORY_ORDER = ["Paintings", "Prints", "Photography", "Islamic Art"];

/** Categories in a stable, curated order (unknown ones sort last). */
const categories: string[] = [];
for (const image of images) {
  if (image.category && !categories.includes(image.category)) {
    categories.push(image.category);
  }
}
categories.sort((a, b) => {
  const indexA = PREFERRED_CATEGORY_ORDER.indexOf(a);
  const indexB = PREFERRED_CATEGORY_ORDER.indexOf(b);
  return (indexA === -1 ? 999 : indexA) - (indexB === -1 ? 999 : indexB);
});

function countFor(filter: string): number {
  if (filter === ALL_FILTER) return images.length;
  return images.filter((image) => image.category === filter).length;
}

function altText(image: GalleryImage): string {
  const parts = [image.title];
  if (image.creator) parts.push(image.creator);
  if (image.date) parts.push(image.date);
  return parts.join(", ");
}

function metaLine(image: GalleryImage): string {
  const parts: string[] = [];
  if (image.creator) parts.push(image.creator);
  if (image.date) parts.push(image.date);
  return parts.join(" · ");
}

function sourceLine(image: GalleryImage): string {
  return `${image.institution} · ${image.rights}`;
}

/* ------------------------------------------------------------------ */
/* Static scaffold                                                     */
/* ------------------------------------------------------------------ */

const app = document.getElementById("app");
if (!app) {
  throw new Error("Gallery root element #app is missing.");
}
app.replaceChildren();

const header = document.createElement("header");
header.className = "site-header";
const title = document.createElement("h1");
title.className = "site-title";
title.textContent = "Open Access Gallery";
const tagline = document.createElement("p");
tagline.className = "site-tagline";
tagline.textContent =
  "Twenty-four public-domain artworks from The Metropolitan Museum of Art Open Access collection and Wikimedia Commons. Every image is stored locally in this project — no remote requests.";
header.append(title, tagline);

const controls = document.createElement("section");
controls.className = "controls";
controls.setAttribute("aria-label", "Gallery controls");
const filtersNav = document.createElement("nav");
filtersNav.className = "filters";
filtersNav.id = "filters";
filtersNav.setAttribute("aria-label", "Filter artworks by category");
const status = document.createElement("p");
status.className = "status";
status.id = "status";
status.setAttribute("role", "status");
status.setAttribute("aria-live", "polite");
controls.append(filtersNav, status);

const main = document.createElement("main");
main.id = "main";
const grid = document.createElement("section");
grid.className = "gallery-grid";
grid.id = "gallery";
grid.setAttribute("aria-label", "Artwork grid");
main.append(grid);

const footer = document.createElement("footer");
footer.className = "site-footer";
const footerText = document.createElement("p");
const metLink = document.createElement("a");
metLink.href = "https://www.metmuseum.org/hubs/open-access";
metLink.textContent = "The Met Open Access (CC0)";
const commonsLink = document.createElement("a");
commonsLink.href = "https://commons.wikimedia.org";
commonsLink.textContent = "Wikimedia Commons (public domain)";
footerText.append(
  "Sources: ",
  metLink,
  " and ",
  commonsLink,
  ". Every image file is stored in public/images/ and described in public/images.json."
);
footer.append(footerText);

/* Lightbox scaffold (the <img> is created on first open so the resting
   document contains exactly one <img> per gallery card). */
const lightbox = document.createElement("div");
lightbox.className = "lightbox";
lightbox.id = "lightbox";
lightbox.setAttribute("role", "dialog");
lightbox.setAttribute("aria-modal", "true");
lightbox.setAttribute("aria-labelledby", "lightbox-title");
lightbox.hidden = true;

const closeButton = document.createElement("button");
closeButton.type = "button";
closeButton.className = "lb-button lb-close";
closeButton.id = "lb-close";
closeButton.setAttribute("aria-label", "Close full-screen viewer");
closeButton.textContent = "✕";

const previousButton = document.createElement("button");
previousButton.type = "button";
previousButton.className = "lb-button lb-nav lb-prev";
previousButton.id = "lb-prev";
previousButton.setAttribute("aria-label", "Previous image");
previousButton.textContent = "←";

const figure = document.createElement("figure");
figure.className = "lb-figure";
const caption = document.createElement("figcaption");
caption.className = "lb-caption";
const lightboxTitle = document.createElement("h2");
lightboxTitle.className = "lb-title";
lightboxTitle.id = "lightbox-title";
const lightboxMeta = document.createElement("p");
lightboxMeta.className = "lb-meta";
const lightboxSource = document.createElement("p");
lightboxSource.className = "lb-source";
caption.append(lightboxTitle, lightboxMeta, lightboxSource);

const nextButton = document.createElement("button");
nextButton.type = "button";
nextButton.className = "lb-button lb-nav lb-next";
nextButton.id = "lb-next";
nextButton.setAttribute("aria-label", "Next image");
nextButton.textContent = "→";

const counter = document.createElement("p");
counter.className = "lb-counter";
counter.id = "lb-counter";
counter.setAttribute("aria-live", "polite");

lightbox.append(closeButton, previousButton, figure, nextButton, counter);

app.append(header, controls, main, footer, lightbox);

/* ------------------------------------------------------------------ */
/* Category filter                                                     */
/* ------------------------------------------------------------------ */

const filterButtons = new Map<string, HTMLButtonElement>();

function buildFilters(): void {
  filtersNav.replaceChildren();
  filterButtons.clear();
  const names = [ALL_FILTER, ...categories];
  for (const name of names) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "filter-button";
    button.dataset.filter = name;
    button.textContent = name;
    const count = document.createElement("span");
    count.className = "filter-count";
    count.setAttribute("aria-hidden", "true");
    count.textContent = String(countFor(name));
    button.append(count);
    button.addEventListener("click", () => setActiveFilter(name));
    filterButtons.set(name, button);
    filtersNav.append(button);
  }
}

let activeFilter = ALL_FILTER;
let visibleImages: GalleryImage[] = images.slice();

function setActiveFilter(filter: string): void {
  activeFilter = filter;
  visibleImages =
    filter === ALL_FILTER
      ? images.slice()
      : images.filter((image) => image.category === filter);
  for (const [name, button] of filterButtons) {
    button.setAttribute("aria-pressed", String(name === filter));
    button.classList.toggle("is-active", name === filter);
  }
  status.textContent = `Showing ${visibleImages.length} of ${images.length} artworks · ${filter}`;
  renderGrid();
}

/* ------------------------------------------------------------------ */
/* Grid                                                                */
/* ------------------------------------------------------------------ */

function buildCard(image: GalleryImage, index: number): HTMLElement {
  const card = document.createElement("figure");
  card.className = "card";
  card.dataset.id = image.id;

  const button = document.createElement("button");
  button.type = "button";
  button.className = "card-button";
  const creatorPhrase = image.creator ? ` by ${image.creator}` : "";
  button.setAttribute(
    "aria-label",
    `View “${image.title}”${creatorPhrase} in the full-screen viewer`
  );

  const img = document.createElement("img");
  img.src = `/images/${image.local_filename}`;
  img.alt = altText(image);
  img.width = image.width;
  img.height = image.height;
  img.loading = "lazy";
  img.decoding = "async";

  const cardCaption = document.createElement("span");
  cardCaption.className = "card-caption";
  const cardTitle = document.createElement("span");
  cardTitle.className = "card-title";
  cardTitle.textContent = image.title;
  const cardMeta = document.createElement("span");
  cardMeta.className = "card-meta";
  cardMeta.textContent = metaLine(image) || image.institution;
  const cardSource = document.createElement("span");
  cardSource.className = "card-source";
  cardSource.textContent = sourceLine(image);
  cardCaption.append(cardTitle, cardMeta, cardSource);

  button.append(img, cardCaption);
  button.addEventListener("click", () => openLightbox(index));
  card.append(button);
  return card;
}

function renderGrid(): void {
  grid.replaceChildren();
  const fragment = document.createDocumentFragment();
  visibleImages.forEach((image, index) => {
    fragment.append(buildCard(image, index));
  });
  grid.append(fragment);
}

/* ------------------------------------------------------------------ */
/* Lightbox                                                            */
/* ------------------------------------------------------------------ */

let lightboxIndex = -1;
let lastFocused: HTMLElement | null = null;
let lightboxImage: HTMLImageElement | null = null;

function ensureLightboxImage(): HTMLImageElement {
  if (lightboxImage) return lightboxImage;
  const img = document.createElement("img");
  img.className = "lb-image";
  img.id = "lightbox-image";
  figure.prepend(img);
  lightboxImage = img;
  return img;
}

function updateLightbox(): void {
  const image = visibleImages[lightboxIndex];
  if (!image) return;
  const img = ensureLightboxImage();
  img.src = `/images/${image.local_filename}`;
  img.alt = altText(image);
  img.style.aspectRatio = `${image.width} / ${image.height}`;
  lightboxTitle.textContent = image.title;
  lightboxMeta.textContent = metaLine(image);
  lightboxSource.replaceChildren();
  const sourceLink = document.createElement("a");
  sourceLink.href = image.source_page;
  sourceLink.textContent = "Source page";
  lightboxSource.append(`${sourceLine(image)}  ·  `, sourceLink);
  if (image.rights_page && image.rights_page !== image.source_page) {
    const rightsLink = document.createElement("a");
    rightsLink.href = image.rights_page;
    rightsLink.textContent = "Rights";
    lightboxSource.append(" · ", rightsLink);
  }
  counter.textContent = `Image ${lightboxIndex + 1} of ${visibleImages.length}`;
}

function openLightbox(index: number): void {
  if (index < 0 || index >= visibleImages.length) return;
  lightboxIndex = index;
  lastFocused =
    document.activeElement instanceof HTMLElement ? document.activeElement : null;
  updateLightbox();
  lightbox.hidden = false;
  document.body.classList.add("lightbox-open");
  closeButton.focus();
}

function closeLightbox(): void {
  if (lightbox.hidden) return;
  lightbox.hidden = true;
  document.body.classList.remove("lightbox-open");
  lightboxIndex = -1;
  if (lastFocused && document.contains(lastFocused)) {
    lastFocused.focus();
  }
  lastFocused = null;
}

function stepLightbox(delta: number): void {
  const count = visibleImages.length;
  if (lightboxIndex === -1 || count === 0) return;
  lightboxIndex = (lightboxIndex + delta + count) % count;
  updateLightbox();
}

function trapFocus(event: Event): void {
  const focusables = Array.from(
    lightbox.querySelectorAll<HTMLElement>("button, a[href]")
  );
  if (focusables.length === 0) return;
  const first = focusables[0];
  const last = focusables[focusables.length - 1];
  const current = document.activeElement as HTMLElement | null;
  if (event instanceof KeyboardEvent && event.shiftKey) {
    if (current === first || !lightbox.contains(current)) {
      event.preventDefault();
      last.focus();
    }
  } else if (current === last || !lightbox.contains(current)) {
    event.preventDefault();
    first.focus();
  }
}

closeButton.addEventListener("click", closeLightbox);
previousButton.addEventListener("click", () => stepLightbox(-1));
nextButton.addEventListener("click", () => stepLightbox(1));
lightbox.addEventListener("click", (event) => {
  if (event.target === lightbox) closeLightbox();
});

document.addEventListener("keydown", (event: KeyboardEvent) => {
  if (lightbox.hidden) return;
  if (event.key === "Escape") {
    event.preventDefault();
    closeLightbox();
  } else if (event.key === "ArrowLeft") {
    event.preventDefault();
    stepLightbox(-1);
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    stepLightbox(1);
  } else if (event.key === "Tab") {
    trapFocus(event);
  }
});

/* ------------------------------------------------------------------ */
/* Boot                                                                */
/* ------------------------------------------------------------------ */

buildFilters();
setActiveFilter(ALL_FILTER);

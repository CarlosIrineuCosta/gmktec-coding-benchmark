import type { GalleryImage } from "./manifest";

export type ActivateHandler = (index: number, trigger: HTMLButtonElement) => void;

interface GalleryViewOptions {
  slot: HTMLElement;
  images: readonly GalleryImage[];
  onActivate: ActivateHandler;
}

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  return node;
}

function tileFor(image: GalleryImage, onActivate: ActivateHandler): HTMLLIElement {
  const tile = el("li", "tile");
  tile.dataset.id = image.id;
  tile.dataset.orientation = image.orientation;
  // Declared box ratio => the tile holds this image's shape before bytes land.
  tile.style.setProperty("--ar", image.ratioCss);

  const figure = el("figure", "tile__figure");

  const trigger = el("button", "tile__trigger");
  trigger.type = "button";
  trigger.dataset.index = String(image.index);
  trigger.dataset.id = image.id;
  trigger.setAttribute(
    "aria-label",
    `Enlarge ${image.title}, by ${image.creator}`,
  );

  const img = el("img", "tile__image");
  img.src = image.src;
  img.alt = image.alt;
  // Intrinsic size plus the declared ratio keep the rendered box locked to the
  // image's real aspect ratio from the first paint onward.
  img.width = image.width;
  img.height = image.height;
  img.decoding = "async";
  img.dataset.orientation = image.orientation;
  img.addEventListener("error", () => tile.dataset.failed = "true", { once: true });
  img.addEventListener("load", () => tile.dataset.loaded = "true", { once: true });
  trigger.append(img);

  const caption = el("figcaption", "tile__caption");
  const title = el("span", "tile__title");
  title.textContent = image.title;
  const byline = el("span", "tile__byline");
  byline.textContent = `${image.creator}${image.year ? ` · ${image.year}` : ""}`;
  const badge = el("span", "tile__badge");
  badge.textContent = `${image.orientation} · ${image.width}×${image.height}`;
  caption.append(title, byline, badge);

  figure.append(trigger, caption);
  tile.append(figure);

  // Enter and Space fire native clicks on the button, so keyboard activation
  // travels through this same path.
  trigger.addEventListener("click", () => onActivate(image.index, trigger));
  return tile;
}

/** Responsive mosaic; each tile is one keyboard-reachable button. */
export function renderGallery({ slot, images, onActivate }: GalleryViewOptions): void {
  slot.textContent = "";

  const list = el("ul", "gallery");
  list.setAttribute("aria-label", "Paintings in the collection");

  const fragment = document.createDocumentFragment();
  for (const image of images) fragment.append(tileFor(image, onActivate));
  list.append(fragment);
  slot.append(list);
}

export function setCountLabel(node: HTMLElement | null, count: number): void {
  if (!node) return;
  node.textContent = count === 1 ? "1 work" : `${count} works`;
}

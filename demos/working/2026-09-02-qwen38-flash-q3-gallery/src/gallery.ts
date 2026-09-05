import { ALL, categoryOptions, worksInCategory } from "./data";
import type { Lightbox } from "./lightbox";
import type { WorkView } from "./types";

/** Build an element with attributes and text/element children (no innerHTML). */
function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attributes: Record<string, string> = {},
  ...children: (Node | string)[]
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) {
    if (name === "class") node.className = value;
    else node.setAttribute(name, value);
  }
  node.append(...children);
  return node;
}

export function slugify(label: string): string {
  return label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

interface GalleryElements {
  grid: HTMLElement;
  filters: HTMLElement;
  status: HTMLElement;
  itemCount: HTMLElement;
  totalCount: HTMLElement;
  activeFilter: HTMLElement;
  emptyState: HTMLElement;
}

/**
 * Renders the grid, the category filter, and the live result summary.
 *
 * Filtering hides cards instead of re-rendering them: the DOM order and every
 * image element stay stable, so a card that opened the lightbox can hand focus
 * straight back to itself when the viewer closes.
 */
export class Gallery {
  private readonly works: WorkView[];
  private readonly lightbox: Lightbox;
  private readonly elements: GalleryElements;
  private readonly cards = new Map<string, HTMLElement>();
  private activeCategory = ALL;
  private visibleWorks: WorkView[];

  constructor(elements: GalleryElements, works: WorkView[], lightbox: Lightbox) {
    this.elements = elements;
    this.works = works;
    this.lightbox = lightbox;
    this.visibleWorks = works;

    this.renderFilters();
    this.renderCards();
    this.elements.grid.addEventListener("click", (event) => this.handleCardActivation(event));
    this.apply(ALL);
  }

  get visible(): WorkView[] {
    return this.visibleWorks;
  }

  private renderFilters(): void {
    const options = categoryOptions(this.works);
    const fragment = document.createDocumentFragment();
    for (const option of options) {
      const isAll = option.label === ALL;
      const count = el("span", { class: "filter__count" }, String(option.count));
      count.setAttribute("aria-hidden", "true");
      const button = el(
        "button",
        {
          class: "filter",
          type: "button",
          "data-filter": "",
          "data-category": option.label,
          "data-testid": isAll ? "filter-all" : `filter-${slugify(option.label)}`,
          "aria-pressed": String(this.activeCategory === option.label),
          title: isAll
            ? `Show all ${option.count} works`
            : `Show the ${option.count} works filed under ${option.label}`
        },
        el("span", { class: "filter__label" }, option.label),
        count
      );
      // Screen readers get "Portraits, 8 items" rather than "Portraits 8".
      button.setAttribute(
        "aria-label",
        isAll ? `Show all categories, ${option.count} works` : `Filter by ${option.label}, ${option.count} works`
      );
      button.addEventListener("click", () => this.apply(option.label));
      fragment.append(button);
    }
    this.elements.filters.append(fragment);
  }

  private renderCards(): void {
    const fragment = document.createDocumentFragment();
    for (const work of this.works) {
      const { record } = work;
      const titleId = `title-${record.id}`;

      const frame = el("span", { class: "card__frame" });
      frame.style.setProperty("--ratio", String(work.ratio));
      const image = el("img", {
        class: "card__image",
        src: work.src,
        alt: work.alt,
        width: String(record.width),
        height: String(record.height),
        decoding: "async",
        "data-testid": "card-image",
        "data-id": record.id
      }) as HTMLImageElement;
      frame.append(image);

      const badge = el("span", { class: "card__badge" }, work.rightsShort);
      const trigger = el(
        "button",
        {
          class: "card__trigger",
          type: "button",
          "data-open": record.id,
          "data-testid": "card-trigger",
          "aria-label": `Open image viewer: ${record.title}, ${work.attribution}`
        },
        frame,
        badge
      ) as HTMLButtonElement;

      const body = el(
        "div",
        { class: "card__body" },
        el("h2", { class: "card__title", id: titleId }, record.title),
        el("p", { class: "card__attribution" }, work.attribution),
        el(
          "p",
          { class: "card__source" },
          el("span", { class: "card__institution" }, record.institution),
          el("span", { class: "card__dot", "aria-hidden": "true" }, "·"),
          el("span", { class: "card__category" }, record.category)
        ),
        el(
          "p",
          { class: "card__file" },
          `${record.width} × ${record.height} px`,
          el("span", { class: "card__dot", "aria-hidden": "true" }, "·"),
          `local ${record.local_filename}`
        ),
        el(
          "a",
          {
            class: "card__link",
            href: record.source_page,
            target: "_blank",
            rel: "noreferrer noopener",
            "data-testid": "card-source-link"
          },
          "Source record"
        )
      );

      const article = el("article", { class: "card__inner", "aria-labelledby": titleId }, trigger, body);
      const card = el("li", {
        class: "card",
        "data-card": "",
        "data-id": record.id,
        "data-category": record.category,
        "data-testid": "gallery-card"
      },
      article);
      this.cards.set(record.id, card);
      fragment.append(card);
    }
    this.elements.grid.append(fragment);
  }

  private handleCardActivation(event: Event): void {
    const target = event.target as HTMLElement | null;
    const trigger = target?.closest<HTMLElement>("[data-open]");
    if (!trigger) return;
    const id = trigger.dataset.open;
    if (!id) return;
    const index = this.visibleWorks.findIndex((work) => work.record.id === id);
    if (index === -1) return;
    event.preventDefault();
    this.lightbox.open(this.visibleWorks, index, trigger);
  }

  /** Apply a category filter and refresh the active state + live summary. */
  apply(category: string): void {
    this.activeCategory = category;
    this.visibleWorks = worksInCategory(this.works, category);

    for (const work of this.works) {
      const card = this.cards.get(work.record.id);
      if (!card) continue;
      const visible = this.visibleWorks.includes(work);
      card.toggleAttribute("hidden", !visible);
      card.setAttribute("aria-hidden", String(!visible));
    }

    for (const button of this.elements.filters.querySelectorAll<HTMLButtonElement>("[data-filter]")) {
      const active = button.dataset.category === category;
      button.setAttribute("aria-pressed", String(active));
      button.classList.toggle("is-active", active);
    }

    const shown = this.visibleWorks.length;
    this.elements.itemCount.textContent = String(shown);
    this.elements.totalCount.textContent = String(this.works.length);
    this.elements.activeFilter.textContent = category === ALL ? "All categories" : category;
    this.elements.status.hidden = false;
    this.elements.emptyState.hidden = shown !== 0;
    this.elements.grid.hidden = shown === 0;
    this.elements.grid.dataset.activeCategory = category;
    void this.matchesFilter;
  }
}

import "./styles.css";
import { buildWorks } from "./data";
import { Gallery } from "./gallery";
import { Lightbox } from "./lightbox";

function mustFind<T extends HTMLElement>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (!element) throw new Error(`page markup is missing "${selector}"`);
  return element;
}

/**
 * Entry point. Everything the gallery renders is bundled at build time from
 * `public/images.json` and served from `public/images/`, so there is no
 * runtime metadata request and no remote image origin.
 */
const works = buildWorks();

const lightbox = new Lightbox(mustFind<HTMLElement>('[data-testid="lightbox"]'));

new Gallery(
  {
    grid: mustFind<HTMLElement>('[data-testid="gallery"]'),
    filters: mustFind<HTMLElement>('[data-testid="filter-bar"]'),
    status: mustFind<HTMLElement>('[data-testid="status"]'),
    itemCount: mustFind<HTMLElement>('[data-testid="item-count"]'),
    totalCount: mustFind<HTMLElement>('[data-testid="total-count"]'),
    activeFilter: mustFind<HTMLElement>('[data-testid="active-filter"]'),
    emptyState: mustFind<HTMLElement>('[data-testid="empty-state"]')
  },
  works,
  lightbox
);

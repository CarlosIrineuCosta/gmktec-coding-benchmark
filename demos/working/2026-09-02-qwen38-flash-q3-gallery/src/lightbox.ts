import type { WorkView } from "./types";

const FOCUSABLE =
  'a[href], button:not([disabled]), input, select, textarea, summary, [tabindex]:not([tabindex="-1"])';

function requireElement<T extends HTMLElement>(root: HTMLElement, selector: string): T {
  const found = root.querySelector<T>(selector);
  if (!found) throw new Error(`lightbox markup is missing "${selector}"`);
  return found;
}

/**
 * Modal viewer for the currently visible works.
 *
 * Keyboard contract: ArrowLeft / ArrowRight move through the filtered set
 * (wrapping at either end), Escape closes, and Tab is trapped inside the
 * dialog while it is open. Closing returns focus to the card control that
 * opened the viewer.
 */
export class Lightbox {
  private readonly root: HTMLElement;
  private readonly panel: HTMLElement;
  private readonly image: HTMLImageElement;
  private readonly title: HTMLElement;
  private readonly attribution: HTMLElement;
  private readonly institution: HTMLElement;
  private readonly rights: HTMLElement;
  private readonly sourceLink: HTMLAnchorElement;
  private readonly downloadLink: HTMLAnchorElement | null;
  private readonly counter: HTMLElement;
  private readonly dimensions: HTMLElement;
  private readonly checksum: HTMLElement | null;
  private readonly previous: HTMLButtonElement;
  private readonly next: HTMLButtonElement;
  private readonly closeButton: HTMLButtonElement;

  private works: WorkView[] = [];
  private index = 0;
  private opener: HTMLElement | null = null;
  private readonly onKeyDown = (event: KeyboardEvent) => this.handleKey(event);

  constructor(root: HTMLElement) {
    this.root = root;
    this.panel = requireElement(root, "[data-lightbox-panel]");
    this.image = requireElement<HTMLImageElement>(root, '[data-testid="lightbox-image"]');
    this.title = requireElement(root, '[data-testid="lightbox-title"]');
    this.attribution = requireElement(root, '[data-testid="lightbox-attribution"]');
    this.institution = requireElement(root, '[data-testid="lightbox-institution"]');
    this.rights = requireElement(root, '[data-testid="lightbox-rights"]');
    this.sourceLink = requireElement<HTMLAnchorElement>(root, '[data-testid="lightbox-source-link"]');
    this.downloadLink = root.querySelector<HTMLAnchorElement>('[data-testid="lightbox-download-link"]');
    this.counter = requireElement(root, '[data-testid="lightbox-counter"]');
    this.dimensions = requireElement(root, '[data-testid="lightbox-dimensions"]');
    this.checksum = root.querySelector<HTMLElement>('[data-testid="lightbox-checksum"]');
    this.previous = requireElement<HTMLButtonElement>(root, '[data-testid="lightbox-prev"]');
    this.next = requireElement<HTMLButtonElement>(root, '[data-testid="lightbox-next"]');
    this.closeButton = requireElement<HTMLButtonElement>(root, '[data-testid="lightbox-close"]');

    for (const target of root.querySelectorAll<HTMLElement>("[data-close]")) {
      target.addEventListener("click", () => this.close());
    }
    this.previous.addEventListener("click", () => this.step(-1));
    this.next.addEventListener("click", () => this.step(1));
  }

  get isOpen(): boolean {
    return !this.root.hasAttribute("hidden");
  }

  /** @param works the visible set, so next/prev follow the active filter */
  open(works: WorkView[], index: number, opener: HTMLElement): void {
    this.works = works;
    this.opener = opener;
    this.root.removeAttribute("hidden");
    this.root.setAttribute("aria-hidden", "false");
    document.documentElement.classList.add("lightbox-open");
    document.addEventListener("keydown", this.onKeyDown, true);
    this.render(index);
    this.closeButton.focus();
  }

  close(): void {
    if (!this.isOpen) return;
    this.root.setAttribute("hidden", "");
    this.root.setAttribute("aria-hidden", "true");
    document.documentElement.classList.remove("lightbox-open");
    document.removeEventListener("keydown", this.onKeyDown, true);
    const target = this.opener?.isConnected ? this.opener : null;
    if (target) {
      target.focus();
      target.scrollIntoView({ block: "nearest" });
    }
    this.opener = null;
  }

  step(delta: number): void {
    if (this.works.length === 0) return;
    const total = this.works.length;
    this.render((this.index + delta + total) % total);
  }

  private render(index: number): void {
    const total = this.works.length;
    if (total === 0) return;
    const clamped = ((index % total) + total) % total;
    const work = this.works[clamped];
    this.index = clamped;

    this.image.src = work.src;
    this.image.alt = work.alt;
    this.image.width = work.record.width;
    this.image.height = work.record.height;
    this.title.textContent = work.record.title;
    this.attribution.textContent = work.attribution;
    this.institution.textContent = work.record.institution;
    this.rights.textContent = work.rightsLong;
    this.sourceLink.href = work.record.source_page;
    this.sourceLink.textContent = new URL(work.record.source_page).host;
    if (this.downloadLink) {
      if (work.record.download_url) {
        this.downloadLink.href = work.record.download_url;
        this.downloadLink.hidden = false;
      } else {
        this.downloadLink.hidden = true;
      }
    }
    this.dimensions.textContent = `${work.record.width} × ${work.record.height} px · local file ${work.record.local_filename}`;
    if (this.checksum) this.checksum.textContent = `SHA-256 ${work.record.sha256}`;
    this.counter.textContent = `${clamped + 1} of ${total}`;

    const single = total <= 1;
    this.previous.disabled = single;
    this.next.disabled = single;
    this.root.dataset.position = String(clamped + 1);
    this.root.dataset.total = String(total);
  }

  private handleKey(event: KeyboardEvent): void {
    if (!this.isOpen) return;
    switch (event.key) {
      case "ArrowLeft":
        event.preventDefault();
        this.step(-1);
        break;
      case "ArrowRight":
        event.preventDefault();
        this.step(1);
        break;
      case "Escape":
        event.preventDefault();
        this.close();
        break;
      case "Tab":
        this.trapFocus(event);
        break;
      default:
        break;
    }
  }

  /** Keep Tab/Shift+Tab inside the dialog while it is open. */
  private trapFocus(event: KeyboardEvent): void {
    const focusable = [...this.panel.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(
      (element) => !element.hasAttribute("hidden") && !element.disabled && element.offsetParent !== null
    );
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const active = document.activeElement as HTMLElement | null;

    if (event.shiftKey && (active === first || !this.panel.contains(active))) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && active === last) {
      event.preventDefault();
      first.focus();
    }
  }
}

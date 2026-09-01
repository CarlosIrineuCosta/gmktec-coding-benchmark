import type { GalleryImage } from "./manifest";

export interface LightboxOptions {
  images: readonly GalleryImage[];
  /**
   * Element made inert while the dialog is open (the gallery shell). The
   * dialog itself must live outside it, otherwise focus restore is impossible.
   */
  inertWhileOpen?: HTMLElement | null;
  onIndexChange?(index: number): void;
}

const SKELETON = `
<div class="lightbox" role="dialog" aria-modal="true" aria-labelledby="lightbox-title" aria-describedby="lightbox-caption" tabindex="-1" hidden>
  <div class="lightbox__scrim" data-close></div>
  <div class="lightbox__panel" data-panel>
    <div class="lightbox__stage">
      <button type="button" class="lightbox__nav lightbox__nav--prev" data-nav="-1" aria-label="Previous image" aria-keyshortcuts="ArrowLeft"><span aria-hidden="true">&larr;</span></button>
      <img class="lightbox__image" alt="" decoding="async" />
      <button type="button" class="lightbox__nav lightbox__nav--next" data-nav="1" aria-label="Next image" aria-keyshortcuts="ArrowRight"><span aria-hidden="true">&rarr;</span></button>
      <p class="lightbox__hint"><span aria-hidden="true">&larr; / &rarr; browse &middot; Esc close</span></p>
    </div>
    <div class="lightbox__aside">
      <header class="lightbox__header">
        <h2 class="lightbox__title" id="lightbox-title"></h2>
        <p class="lightbox__byline"></p>
      </header>
      <p class="lightbox__caption" id="lightbox-caption"></p>
      <dl class="lightbox__meta"></dl>
      <a class="lightbox__source" target="_blank" rel="noopener noreferrer">Source page<span class="visually-hidden"> (opens in a new tab)</span></a>
      <div class="lightbox__toolbar">
        <p class="lightbox__status" role="status" aria-live="polite"></p>
        <button type="button" class="lightbox__close" data-close aria-label="Close image viewer" aria-keyshortcuts="Escape">Close</button>
      </div>
    </div>
  </div>
</div>`;

const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

type Reason = "opened" | "next" | "previous" | "jump";

/**
 * Modal viewer for the gallery. It mounts beside the app shell so the shell
 * can be made inert while the dialog is open, which keeps the focus loop
 * honest and the return-focus target reachable.
 */
export class Lightbox {
  private readonly images: readonly GalleryImage[];
  private readonly inertTarget: HTMLElement | null;
  private readonly options: LightboxOptions;
  private readonly host: HTMLElement;
  private readonly dialog: HTMLElement;
  private readonly image: HTMLImageElement;
  private readonly titleEl: HTMLElement;
  private readonly bylineEl: HTMLElement;
  private readonly captionEl: HTMLElement;
  private readonly metaEl: HTMLElement;
  private readonly sourceEl: HTMLAnchorElement;
  private readonly statusEl: HTMLElement;
  private readonly handleKeyDown = (event: KeyboardEvent) => this.onKeyDown(event);
  private readonly handleClick = (event: MouseEvent) => this.onClick(event);
  private opener: HTMLElement | null = null;
  private shown = 0;
  private isOpen = false;
  private savedPadding = "";

  constructor(options: LightboxOptions) {
    this.options = options;
    this.images = options.images;
    this.inertTarget = options.inertWhileOpen ?? null;

    this.host = document.createElement("div");
    this.host.id = "lightbox-root";
    this.host.innerHTML = SKELETON;
    document.body.append(this.host);

    const root = this.host.firstElementChild as HTMLElement;
    this.dialog = root;
    this.image = root.querySelector<HTMLImageElement>(".lightbox__image")!;
    this.titleEl = root.querySelector<HTMLElement>(".lightbox__title")!;
    this.bylineEl = root.querySelector<HTMLElement>(".lightbox__byline")!;
    this.captionEl = root.querySelector<HTMLElement>(".lightbox__caption")!;
    this.metaEl = root.querySelector<HTMLElement>(".lightbox__meta")!;
    this.sourceEl = root.querySelector<HTMLAnchorElement>(".lightbox__source")!;
    this.statusEl = root.querySelector<HTMLElement>(".lightbox__status")!;
  }

  get open(): boolean {
    return this.isOpen;
  }

  get currentIndex(): number {
    return this.shown;
  }

  openAt(index: number, opener?: HTMLElement | null): void {
    if (!this.images.length) return;
    if (!this.isOpen) {
      this.opener = (opener ?? (document.activeElement as HTMLElement | null)) || null;
    }
    this.isOpen = true;
    this.shown = this.clamp(index);
    this.dialog.hidden = false;
    this.lockScroll();
    document.addEventListener("keydown", this.handleKeyDown, true);
    document.addEventListener("click", this.handleClick);
    this.paint("opened");
    this.preloadNeighbours();
    // Focus the dialog itself: assistive tech then reads the whole thing and
    // key events land on us regardless of what was clicked.
    this.dialog.focus({ preventScroll: true });
    // Only inert the background once our own focus is settled.
    this.inertTarget?.setAttribute("inert", "");
  }

  close(): void {
    if (!this.isOpen) return;
    this.isOpen = false;
    this.dialog.hidden = true;
    document.removeEventListener("keydown", this.handleKeyDown, true);
    document.removeEventListener("click", this.handleClick);
    this.unlockScroll();
    // Reveal the shell again *before* restoring focus, or the focus call is a
    // silent no-op against an inert subtree.
    this.inertTarget?.removeAttribute("inert");
    const target = this.opener;
    this.opener = null;
    if (target && target.isConnected) {
      target.focus({ preventScroll: true });
      target.scrollIntoView({ block: "nearest" });
    }
  }

  next(): void {
    this.goTo(this.shown + 1, "next");
  }

  previous(): void {
    this.goTo(this.shown - 1, "previous");
  }

  goTo(index: number, reason: Reason = "jump"): void {
    if (!this.isOpen) return;
    this.shown = this.clamp(index);
    this.paint(reason);
    this.preloadNeighbours();
  }

  private clamp(index: number): number {
    const total = this.images.length;
    if (!total) return 0;
    return ((index % total) + total) % total;
  }

  private current(): GalleryImage {
    const image = this.images[this.shown];
    if (!image) throw new Error(`no gallery image at index ${this.shown}`);
    return image;
  }

  private paint(reason: Reason): void {
    const image = this.current();
    this.image.alt = image.alt;
    this.image.src = image.src;
    this.image.dataset.orientation = image.orientation;
    this.image.style.setProperty("--ar", image.ratioCss);
    this.dialog.dataset.orientation = image.orientation;

    this.titleEl.textContent = image.title;
    this.bylineEl.textContent = `${image.creator}${image.year ? ` · ${image.year}` : ""}`;
    this.captionEl.textContent = image.caption;
    this.sourceEl.href = image.sourcePage || "#";
    this.sourceEl.toggleAttribute("inert", !image.sourcePage);

    const rows: Array<[string, string]> = [
      ["Artist", image.creator],
      ["Date", image.year ?? "Undated"],
      ["Medium", image.medium ?? "Not recorded"],
      ["Repository", image.repository ?? "Not recorded"],
      ["File", `${image.filename} · ${image.width}×${image.height} px`],
      ["Framing", `${image.orientation}, ratio ${image.ratio.toFixed(2)}:1`],
      ["Rights", image.licenseLabel],
    ];
    if (image.sha256) rows.push(["SHA-256", `${image.sha256.slice(0, 16)}…`]);

    this.metaEl.textContent = "";
    for (const [term, value] of rows) {
      const dt = document.createElement("dt");
      dt.textContent = term;
      const dd = document.createElement("dd");
      dd.textContent = value;
      this.metaEl.append(dt, dd);
    }

    this.announce(reason);
    this.options.onIndexChange?.(this.shown);
  }

  private announce(reason: Reason): void {
    const image = this.current();
    const verb =
      reason === "next"
        ? "Next:"
        : reason === "previous"
          ? "Previous:"
          : reason === "opened"
            ? "Viewing:"
            : "Now showing:";
    this.statusEl.textContent =
      `${verb} ${this.shown + 1} of ${this.images.length}. ${image.title}, ${image.creator}. ` +
      `${image.width} by ${image.height} pixels, ${image.orientation}. ${image.licenseLabel}.`;
  }

  private preloadNeighbours(): void {
    for (const delta of [1, -1]) {
      const neighbour = this.images[this.clamp(this.shown + delta)];
      if (!neighbour) continue;
      const preload = new Image();
      preload.src = neighbour.src;
    }
  }

  private onKeyDown(event: KeyboardEvent): void {
    if (!this.isOpen || event.defaultPrevented) return;
    switch (event.key) {
      case "Escape":
        event.preventDefault();
        this.close();
        break;
      case "ArrowRight":
        event.preventDefault();
        this.next();
        break;
      case "ArrowLeft":
        event.preventDefault();
        this.previous();
        break;
      case "Home":
        event.preventDefault();
        this.goTo(0);
        break;
      case "End":
        event.preventDefault();
        this.goTo(this.images.length - 1);
        break;
      case "Tab":
        this.trapFocus(event);
        break;
      default:
        break;
    }
  }

  private trapFocus(event: KeyboardEvent): void {
    const focusables = [...this.dialog.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(
      (node) => node.getClientRects().length > 0,
    );
    if (!focusables.length) {
      event.preventDefault();
      this.dialog.focus();
      return;
    }
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (!first || !last) {
      event.preventDefault();
      this.dialog.focus();
      return;
    }
    const active = document.activeElement as HTMLElement | null;
    const inside = Boolean(active && this.dialog.contains(active));

    if (event.shiftKey) {
      if (!inside || active === first || active === this.dialog) {
        event.preventDefault();
        last.focus();
      }
    } else if (!inside || active === last) {
      event.preventDefault();
      first.focus();
    }
  }

  private onClick(event: MouseEvent): void {
    if (!this.isOpen) return;
    const target = event.target as Element | null;
    if (!target) return;

    const nav = target.closest<HTMLElement>("[data-nav]");
    if (nav && this.dialog.contains(nav)) {
      event.preventDefault();
      if (Number(nav.dataset.nav) < 0) this.previous();
      else this.next();
      return;
    }

    // Only a [data-close] that lives inside the dialog counts: the click that
    // opened the viewer (on a tile in the shell) must not close it instantly.
    const closer = target.closest("[data-close]");
    if (closer && this.dialog.contains(closer)) {
      event.preventDefault();
      this.close();
    }
  }

  private lockScroll(): void {
    const gutter = window.innerWidth - document.documentElement.clientWidth;
    this.savedPadding = document.documentElement.style.paddingRight;
    if (gutter > 0) document.documentElement.style.paddingRight = `${gutter}px`;
    document.documentElement.classList.add("modal-open");
  }

  private unlockScroll(): void {
    document.documentElement.style.paddingRight = this.savedPadding;
    this.savedPadding = "";
    document.documentElement.classList.remove("modal-open");
  }
}

import manifest from "virtual:gallery-manifest";
import { normalizeManifest } from "./manifest";
import { renderGallery, setCountLabel } from "./gallery-view";
import { Lightbox } from "./lightbox";
import "./styles/gallery.css";

function boot(): void {
  const images = normalizeManifest(manifest);
  const slot = document.getElementById("gallery");
  const shell = document.getElementById("app");
  setCountLabel(document.getElementById("gallery-count"), images.length);

  if (!slot) return;
  if (!images.length) {
    slot.textContent = "The image manifest is empty, so there is nothing to display.";
    return;
  }

  const lightbox = new Lightbox({ images, inertWhileOpen: shell });

  renderGallery({
    slot,
    images,
    onActivate: (index, trigger) => lightbox.openAt(index, trigger),
  });

  // Cheap observable summary for harnesses/reviewers; renders nothing itself.
  document.documentElement.dataset.galleryCount = String(images.length);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot, { once: true });
} else {
  boot();
}

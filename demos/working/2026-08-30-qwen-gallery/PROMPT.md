# Exact candidate prompt

The following was supplied as the initial user message to the retained Qwen
gallery candidate. It is reproduced exactly, including the canonical task
packet.

```text
You are the implementation candidate for a fresh isolated gallery workspace. Complete this canonical task packet using only the provided tools and files. Do not edit TASK.md or tests/gallery.spec.ts. Implement and validate the gallery, then state clearly when complete.

--- Canonical task packet ---
# Greenfield gallery task contract

Build a responsive photo gallery from the supplied local public-domain/CC0
image corpus and its `images.json` manifest. The candidate may change only its
fresh disposable worktree.

Observable acceptance requires:

1. every manifest image renders with non-empty alternative text and a caption;
2. mixed portrait, landscape, and square images retain their aspect ratio;
3. activating an image opens a lightbox with caption/metadata;
4. previous/next controls and ArrowLeft/ArrowRight move through items;
5. Escape closes the lightbox and returns meaningful focus;
6. the gallery remains usable at a 390 px mobile viewport and 1440 px desktop
   viewport;
7. there are no failed image requests or browser console errors.

The task packet deliberately does not prescribe component structure, CSS
framework, masonry algorithm, or internal state architecture. Standardized
Playwright screenshots are evidence for Charles's visual review, not a hidden
aesthetic score.
```

The later recorded I1/I2/I3 supervisory messages are in
[`README.md`](README.md#coordinator-corrections).

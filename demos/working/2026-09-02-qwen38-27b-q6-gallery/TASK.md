# Gallery concept extension task

Build a polished, local-only photo gallery in this disposable workspace.

The workspace starts with 12 supplied public-domain images in `public/images/`
and their records in `public/images.json`. Keep all supplied images.

## Research and asset requirements

Find, rights-check, download, and add exactly 12 more images. Use only these
two sources:

- The Metropolitan Museum of Art Open Access collection. Use only items marked
  Open Access/public domain. Record `institution: "The Metropolitan Museum of
  Art"` and `rights: "CC0"`.
- The Library of Congress. Use only an item whose item-level Rights Advisory
  states `Public Domain` or `No Known Copyright Restrictions`. Record
  `institution: "Library of Congress"` and the matching `rights` value
  (`"public-domain"` or `"no-known-copyright-restrictions"`).

For each added record, put a local image file in `public/images/` and record:
`id`, `local_filename`, `title`, `creator` when available, `date` when
available, `institution`, `rights`, `source_page`, `rights_page`,
`download_url`, `sha256`, `width`, `height`, and `category`.

For Met research and downloads, use only the provided command:
`python3 tools/met_open_access.py`. It accesses only The Met's documented
Open Access endpoints and verifies the returned object is public domain before
it downloads a local image. Do not use direct `curl` or arbitrary network
commands. The prohibition on a remote application API applies to the finished
gallery, not to this bounded acquisition tool.

Do not use external images at runtime. Do not use credentials, accounts,
uploads, a database, or a remote application API.

## Product requirements

- Show all 24 local images with useful alternative text, captions, and source
  metadata.
- Use a responsive layout for mixed portrait, landscape, and square images.
- Provide a lightbox with previous/next controls, ArrowLeft/ArrowRight, and
  Escape-to-close with useful focus return.
- Add a category filter with an `All` control and at least three non-empty
  categories. Show the active filter and a useful item count.
- Provide usable 390 px mobile and 1440 px desktop layouts.
- Keep the application local-only after the download pass. There must be no
  failed image requests or browser console errors.

## Completion

Do not edit `TASK.md` or files in `tests/`. Run the build and browser tests.
State what you completed and any remaining limitation.

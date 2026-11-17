# crypto-tools

A collection of cryptanalysis tools and utilities for classical cipher analysis, shared publicly for anyone working on similar problems.

## Contents

- `tools/` — Python and other CLI-based cryptanalysis scripts.
- `docs/` — Browser-based HTML+JS tools (some are translations of the Python scripts in `tools/`). This folder is served live as a static site.

## GitHub Pages

This site is published via GitHub Pages, configured to deploy from `main` / `docs`. Each HTML+JS tool lives in its own subfolder of `docs/` (e.g. `docs/stethoscope/`) and becomes part of the live site, linked from `docs/index.html`. Shared scripts, styles and images are in `docs/js/`, `docs/css/` and `docs/graphics/`.

Every page links `docs/css/site.css`, which holds the shared fonts and colours (including dark mode). Guides and specs written in Markdown are converted with pandoc and also use `docs/css/document.css`; run this from the page's folder:

```
pandoc -s NAME.md -o NAME.html --css ../css/site.css --css ../css/document.css
```

## License

See [LICENSE](LICENSE).

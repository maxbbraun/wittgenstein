# Vollkorn

Source: [Friedrich Althausen's official repository](https://github.com/FAlthausen/Vollkorn-Typeface/tree/38ab7a896bd6b163ac7f834ec696d6c68e5dedd6), revision `38ab7a896bd6b163ac7f834ec696d6c68e5dedd6`.

These WOFF2 files derive from `fonts/variable/Vollkorn[wght].ttf` and `fonts/variable/Vollkorn-Italic[wght].ttf`, version 5.000. Their outlines match the version 5.001 files previously served by Google Fonts, which only changed version metadata. See `OFL.txt` and `Fontlog.txt` for licensing and upstream history.

Only weights 400 and 600 are used. Source interpolation is retained because trimming the weight axis rounds glyph outlines and advances at 600. Glyph names and original font bounds are retained, and the global scan-control program is omitted, matching the previous web fonts' rendering metadata. Subsets retain normal shaping (kerning, ligatures, language forms, and combining marks), with unused optional stylistic features omitted. Character coverage, including composition helpers, is recorded in `scripts/vollkorn-subsets.json`.

Every page uses regular Latin and Greek, so they share one file. Italic Latin remains separate; other scripts load only when their characters are used. The two core files are preloaded. App Engine serves this versioned directory as static content with a one-year cache lifetime. Change the directory version and template URLs whenever published font assets change.

To reproduce the assets, install `fonttools[woff]==4.64.0` and `brotli==1.2.0` in a temporary environment, then run `python scripts/build_fonts.py` from the repository. The script downloads only the pinned official sources and verifies their SHA-256 hashes. No font build tools are required at runtime.

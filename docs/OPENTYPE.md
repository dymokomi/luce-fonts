# Font files and shaping: `opentype` and `shaping`

Two portable modules read font files and shape text in pure Luce, with no platform library:
the same code on macOS, Windows and Linux, and the same numbers on each. They began as the
font engine of the Luce port of Ladybird (luce-browser-render's `web_fonts`, which now sits
on them), where they replace Skia's FreeType backend and HarfBuzz; the browser's oracle tests,
printed by Ladybird's own LibGfx over Skia, FreeType and HarfBuzz 10.2, now run here and pin
the numbers bit for bit.

The platform module `fonts` (CoreText, GDI, cairo) is separate and unchanged.

## `opentype`: faces, glyphs and metrics

```luce
from luce_fonts import opentype

let face = try opentype.sfnt_face_create(bytes, 0)      # .ttf/.otf; a .ttc's font 0
let glyph = opentype.sfnt_face_glyph_for_code_point(face, (u32)'A')
let advance = opentype.sfnt_face_advance(face, glyph)    # font units
var path = opentype.sfnt_face_glyph_path(face, glyph, 16.0)  # at 16 px, y down
defer path.release()
let metrics = opentype.sfnt_face_metrics(face, 16.0)     # ascent < 0, descent > 0
opentype.sfnt_face_destroy(face)                         # the bytes stay the caller's
```

- **The face** (`reader.lucb`): `SfntFace` from the bytes of an sfnt file (TrueType or CFF
  outlines, collections by index), with its table directory, head, maxp, hhea, OS/2 and
  post fields, FreeType's ascender/descender/height and style flags, the family name as
  FreeType chooses it (`family_name`), and Skia's weight, width and slope
  (`sfnt_face_weight`, `_width`, `_slope`). `sfnt_face_table(face, sfnt_tag(...))` gives
  any table's bytes; the `sfnt_u16`-style readers are bounds-checked and answer 0 past the
  data, so a malformed font gives odd numbers, never a trap. The bytes are borrowed: keep
  them alive while the face is in use. A face holds what it allocated (from the allocator
  current when it was made) until `sfnt_face_destroy`.
- **Characters to glyphs** (`cmap.lucb`): cmap formats 0, 4, 6, 10, 12 and 13.
  `sfnt_face_glyph_for_code_point` takes the subtable HarfBuzz would,
  `sfnt_face_ft_glyph_for_code_point` the Unicode charmap FreeType would (they can differ).
- **Outlines** (`glyf.lucb`, `cff.lucb`): TrueType simple and composite glyphs with
  FreeType's fixed-point arithmetic, CFF and CFF2 Type 2 charstrings (CID-keyed fonts too;
  CFF2 at its default instance). `sfnt_face_glyph_path(face, glyph, pixel_size)` is the
  `GlyphPath` Skia's `SkFont::getPath` builds: move, line, quad, cubic and close verbs over
  `GlyphPoint`s in pixels, y growing downward, the origin on the baseline at the pen
  position; a path at `units_per_em` pixels is in font units. `sfnt_face_load_outline`
  gives FreeType's raw 26.6 outline.
- **Metrics at a size** (`scaler.lucb`): `sfnt_face_metrics(face, pixel_size)` is
  `SkFont::getMetrics` (Skia's FreeType scaler context: typographic or hhea metrics, the
  x-height from OS/2 or the 'x' glyph, sizes above 256 px measured at 64 and scaled, a zero
  size measured at 1 px), `sfnt_face_hinted_advance` a glyph's advance as Skia's glyph
  cache has it (phantom points rounded to whole pixels), `sfnt_face_measure_ascii` and
  `sfnt_face_bounds`.
- **Web fonts** (`woff.lucb`): `woff_to_sfnt(bytes)` unwraps a WOFF file (zlib tables
  through luce-compress) with Ladybird's checks.
- **WOFF2** (`woff2.lucb`, `woff2_glyf.lucb`, `woff2_rebuild.lucb`): `woff2_to_sfnt(bytes)`
  decodes a WOFF 2.0 file as Google's woff2 reference decoder does (the library behind
  Ladybird's `WOFF2::convert_to_ttf`), byte for byte: the header and table directory
  (known tags, UIntBase128 and 255UInt16 numbers), collections, the Brotli stream (luce-compress's
  `brotli`), the glyf/loca transform (seven streams, composites, the overlap bitmap, the bbox
  stream, instructions, either loca format) and the hmtx transform, with table checksums and
  head's checkSumAdjustment. It accepts and refuses what the reference does, bounded by the
  reference's compression-ratio check and woff2_decompress's 128 MiB output limit
  (`woff2_max_sfnt_size`).
- `List[T]` (`list.lucb`) is the growable array the two modules build outlines and glyph
  runs in; it keeps the allocator it first grew in, so a list made under an arena or a
  collected heap stays there.

Not implemented: TrueType hinting (outlines are unhinted, as Skia asks for paths), variable
font instancing (variations are recorded, the default instance is drawn), color glyphs
(COLR, CBDT, sbix and SVG tables are only there to be found), bitmap-only fonts.

## `shaping`: HarfBuzz's default shaper

```luce
from luce_fonts import shaping

let font = shaping.hb_font_create(shaping.hb_face_create(shaping.hb_blob_create(bytes), 0))
shaping.hb_font_set_scale(font, 16 * 64, 16 * 64)     # positions in 1/64 px at 16 px
let buffer = shaping.hb_buffer_create()
defer shaping.hb_buffer_destroy(buffer)
shaping.hb_buffer_add_utf16(buffer, units)            # or hb_buffer_add_ascii
shaping.hb_buffer_guess_segment_properties(buffer)    # or hb_buffer_set_direction
shaping.hb_shape(font, buffer, features)              # HbFeature: tag, value, start, end
let infos = shaping.hb_buffer_get_glyph_infos(buffer)         # codepoint = glyph, cluster
let positions = shaping.hb_buffer_get_glyph_positions(buffer) # advances and offsets
```

The API follows HarfBuzz's, and so does the work, in HarfBuzz's order: clusters (marks,
joiners, emoji modifiers and tags join the grapheme before them), the normalizer
(decomposition of what the font lacks, the space fallbacks, canonical reordering of marks,
recomposition), GDEF classes, the default features (`ccmp`, `locl`, `rlig`, `calt`, `clig`,
`liga`, `kern`, `mark`, `mkmk`, ...) overridden by the caller's, GSUB lookups 1–7, GPOS
lookups 1, 2, 4–9 or the legacy `kern` table, AAT `trak`, zero-width marks, HarfBuzz's
fallback mark positioning for fonts without GPOS, and right-to-left runs reversed.

Not implemented: the complex-script shapers (Arabic joining, Indic, USE, Thai, Hangul, ...),
GSUB 8, GPOS 3 (cursive), device tables, FeatureVariations, AAT `morx`/`kerx` and variation
selectors; the fragments' FIXMEs name the details.

Its Unicode properties are HarfBuzz's: general categories of marks, scripts and the Emoji
property come from `src/shaping/unicode_tables.lucb`, generated by
`tools/shaping_unicode.py` from the Unicode Character Database (17.0.0, the version of
luce-std's unicode module, which supplies combining classes and NFD/NFC); rerun the tool to
move to a newer Unicode.

## Tests

`src/opentype/tests_oracle.lucb` and `src/shaping/tests_oracle.lucb` hold the browser
oracle's cases for the faces, glyph ids, metrics at fifteen sizes and glyph paths of the
four test fonts (SerenitySans, Lato Bold, Noto Emoji and the CFF Noto Sans Tifinagh), the
shaping of 33 texts (ligatures, kerning, marks, emoji sequences, right-to-left text, letter
spacing, missing glyphs) and a WOFF font, compared bit for bit. They are printed by
`oracles/luce-browser-render/fonts/gen_tests.cpp` in luce-browser-tools, through Ladybird's
Gfx::Font, so the test bodies (`tests_support.lucb`) compute what Gfx::Font computes from
these modules: a font of `p` points is `p × 96 / 72` pixels, and shaped glyphs are laid out
from a baseline at (3.5, 20.25) as `Gfx::shape_text` lays them out. The oracle's text-blob
bounds and glyph intercept cases test Ladybird's GlyphRun and stay in luce-browser-render.
`tests_units.lucb` ports Ladybird's TestWOFF and TestWOFF2 and checks the readers' helpers.
`tests_woff2.lucb` decodes the files of `tests/woff2` and compares them byte for byte with
the sfnt Google's woff2_decompress made of each (a TrueType font with composites and
instructions, a CFF font, the hmtx transform with overlap bits, and a collection sharing its
glyf), checks the decoded Lato Bold glyph by glyph against the original, and decodes
mutated files, which must fail or decode but never trap.
The test fonts are in `tests/fonts` with their licences (`NOTICE`).

## Licences

These modules are a derived work of the Luce port of Ladybird (BSD 2-Clause,
`LICENSE-luce-browser`) and follow FreeType, HarfBuzz and Skia (`LICENSE-skia`) in what they
compute; they carry no code of those projects.

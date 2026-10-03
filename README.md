# luce-fonts

Fonts for Luce: native font rasterisation (glyph coverage and metrics from the platform's
text engine), and a portable font engine in pure Luce that reads OpenType, TrueType, CFF and
WOFF files and shapes text as HarfBuzz does.

## Modules

| import | what it holds |
| --- | --- |
| `import fonts` | Native font resources, grayscale rasterization and terminal cell widths (`cells`, `text_cells`) |
| `import opentype` | Font files without a platform library: faces of sfnt files and collections, cmaps, TrueType and CFF outlines as paths, FreeType/Skia-exact metrics at a size, WOFF unwrapping |
| `import shaping` | HarfBuzz's default shaper over `opentype`: GSUB, GPOS and kern, marks, clusters, right-to-left runs |

`docs/FONTS.md` describes the native module, `docs/OPENTYPE.md` the font engine (its API,
limits, Unicode data and oracle tests).

## Using it

Add the dependency to `package.prisma`; the modules keep their short names:

```prisma
def dependency "luce-fonts" {
    str owner = "dymokomi"
    str version = "^0.1.0"
}
```

## Depends on

- luce-std
- luce-compress (WOFF's zlib tables)

## Platforms

macOS (CoreText), Windows (GDI), Linux (cairo).

Native libraries it links, by platform (declared in `package.prisma`, linked only when the program reaches code that needs them):

- macos: CoreText, CoreGraphics, CoreFoundation
- windows: gdi32
- linux: cairo

## Tests

`./test.sh` runs every module's `test` blocks and the unit tests through the native and C backends, then the program checks under `tests/programs`. It expects the compiler beside this checkout at `../luce-base/build/luce-base` (or `--base PATH`).

## License

MIT or Apache-2.0, at your option. The `opentype` and `shaping` modules come from the Luce
port of Ladybird and are also under its BSD 2-Clause licence (`LICENSE-luce-browser`); they
follow Skia (`LICENSE-skia`), FreeType and HarfBuzz in what they compute. The test fonts carry
their own licences (`tests/fonts/NOTICE`).

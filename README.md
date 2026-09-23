# luce-fonts

Native font rasterisation: glyph coverage and metrics from the platform's text engine.

## Modules

| import | what it holds |
| --- | --- |
| `import fonts` | Native font resources and grayscale rasterization |

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

## Platforms

macOS (CoreText), Windows (GDI), Linux (cairo).

Native libraries it links, by platform (declared in `package.prisma`, linked only when the program reaches code that needs them):

- macos: CoreText, CoreGraphics, CoreFoundation
- windows: gdi32
- linux: cairo

## Tests

`./test.sh` runs every module's `test` blocks and the unit tests through the native and C backends, then the program checks under `tests/programs`. It expects the compiler beside this checkout at `../luce-base/build/luce-base` (or `--base PATH`).

## License

MIT or Apache-2.0, at your option.

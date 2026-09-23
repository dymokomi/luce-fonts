# Native fonts and coverage drawing

`fonts.Face(size = 14.0, family = "")` loads an installed monospace face and
reports point-space advance, ascent and descent. `Face.rasterize(text, scale)`
returns an owned, tightly packed, top-down grayscale `Bitmap`; close it explicitly
in Base. An empty family selects Menlo on macOS, Consolas on Windows and the
fontconfig monospace family on Linux. Loading and rasterization require the main
thread. Invalid UTF-8, control characters, non-monospace faces and invalid sizes
are recoverable errors. A text run is limited to 4096 bytes / 1024 scalars, and a
raster to 4 MiB. Installed-family matching follows the host font service.

Platform calls stay under `src/luce_fonts/fonts/{macos,windows,linux}`. CoreText and
CoreGraphics provide macOS glyphs and fallback. Windows uses GDI outline coverage,
converting its 0..64 grayscale samples into 0..255 alpha and removing DWORD row
padding. Linux uses Cairo's fontconfig/FreeType integration and A8 surfaces;
applications that use fonts need Cairo and an installed monospace face. Native
link requirements are declared alongside each adapter. Importing unrelated
standard modules does not add font libraries to an executable.

The first API is deliberately code-grid text: one Unicode scalar per cell,
without contextual shaping or bidirectional layout. Windows currently replaces
supplementary-plane scalars. Font-file registration, color emoji, grapheme-aware
layout and paragraph shaping are not part of this interface yet. `luce-ui.Font`
adds shared ownership and a bounded raster cache; the standard library does not
own widget styling or global typography state.

`gpu.RenderTarget.mask(pixels, width, height, rectangle, color)` copies 8-bit
coverage into its frame and tints it with a linear-light color. The rectangle is
in logical points. Both Metal and Vulkan bilinearly sample the same packed
coverage words from a storage buffer and blend into the sRGB target. This is six
vertices per text run, with no geometry per glyph pixel. Storage is limited to
16 MiB per frame in addition to the existing geometry/command limits. Coverage
and geometry share the checked target's clipping and lifetime.

The UI raster cache avoids repeating native font work for unchanged runs. Uploads
currently belong to each frame; a persistent GPU atlas is a future optimization,
not an application resource-management requirement.

`tests/programs/fonts/run.py` checks metrics, transparent blank glyphs, intermediate
alpha, multiple backing scales, limits, frame expiry and foreign-symbol isolation
in all native optimization levels and both C comparison modes. UI pixel tests
read back real Metal rendering, including known transparent/partial/opaque masks.
The Vulkan declarations are checked against the Khronos header ABI on Windows;
Windows font behavior runs on the Windows CI host. A Windows Vulkan device is
still needed to verify presentation pixels there.

Implementation references: [CoreText fonts](https://developer.apple.com/documentation/coretext/ctfont),
[CoreGraphics bitmap contexts](https://developer.apple.com/documentation/coregraphics/cgcontext/init(data:width:height:bitspercomponent:bytesperrow:space:bitmapinfo:)),
[GDI glyph coverage](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-getglyphoutlinew),
[Cairo text](https://www.cairographics.org/manual/cairo-text.html),
[the Vulkan registry](https://github.com/KhronosGroup/Vulkan-Headers/tree/v1.3.296/registry).

#!/usr/bin/env python3
"""Exercise system fonts without a window or display server, and check OS isolation."""
import argparse
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('compiler', type=Path, nargs='?', default=ROOT.parent / 'luce-base/build/luce-base')
a = p.parse_args()
with tempfile.TemporaryDirectory(prefix='luce-fonts-') as temporary:
    binary = Path(temporary) / 'fonts'
    source = ROOT / 'tests/programs/fonts/main.lucb'
    for flags in [["--native", "--opt", str(n)] for n in range(4)] + [["--backend=c"], ["--backend=c", "--release"]]:
        subprocess.run([str(a.compiler.resolve()), 'build', str(source), *flags, '-o', str(binary)], check=True, timeout=120)
        subprocess.run([str(binary)], check=True, timeout=30)
    for target in ['arm64-macos', 'x86_64-windows', 'x86_64-linux']:
        output = Path(temporary) / 'fonts.s'
        subprocess.run([str(a.compiler.resolve()), 'build', str(source), '--target', target, '--emit=asm', '-o', str(output)], check=True, timeout=120)
        assembly = output.read_text()
        foreign = []
        if not target.endswith('macos'): foreign += ['CTFontCreateWithName', 'CGContextRelease']
        if not target.endswith('windows'): foreign += ['CreateFontIndirectW', 'GetGlyphOutlineW']
        if not target.endswith('linux'): foreign += ['cairo_create', 'cairo_scaled_font_destroy']
        assert not any(symbol in assembly for symbol in foreign), target
        print('PASS native font boundary', target)

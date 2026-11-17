#!/usr/bin/env python3
"""Regenerate the course figures in src/static/img/learn/.

    python3 tools/build-figures.py

Figures are drawn by the small functions in tools/figures/. The SVG files are
committed, so the site build does not need to run this.
"""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'figures'))
n = 0
for name in ('m01_05', 'm06_10', 'm11_14'):
    try:
        mod = importlib.import_module(name)
    except ModuleNotFoundError:
        continue
    for fn in mod.ALL:
        fn()
        n += 1
print('wrote %d figures' % n)

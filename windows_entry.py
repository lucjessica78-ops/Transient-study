"""
Entry point used by PyInstaller to build a standalone executable.

This just calls the same CLI as `snubber-analyzer --config ...` would when
pip-installed -- it exists as a separate file because PyInstaller works best
pointed at a plain script rather than a package's console-script entry point.
"""

import sys
from snubber_analyzer.cli import main

if __name__ == "__main__":
    sys.exit(main())

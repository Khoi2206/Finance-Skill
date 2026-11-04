#!/usr/bin/env python3
"""Điểm vào dòng lệnh của công cụ #4 (board pack). Xem boardpack/cli.py hoặc README.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from boardpack.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

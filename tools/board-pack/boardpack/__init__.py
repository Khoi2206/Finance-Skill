"""Công cụ #4 — bộ tự tạo báo cáo quản trị tháng / báo cáo HĐQT (PPTX) từ warehouse alta-finance-intelligence."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
AFI_SRC = REPO / "alta-finance-intelligence" / "src"
if AFI_SRC.exists() and str(AFI_SRC) not in sys.path:
    sys.path.insert(0, str(AFI_SRC))

__version__ = "0.1.0"

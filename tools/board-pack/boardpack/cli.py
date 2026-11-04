"""Tạo board pack PPTX.

  python tools/board-pack/build_board_pack.py --month 2026-10 [--mode month|ytd] [--plan plan.csv]
  afi boardpack --month 2026-10 --mode ytd --plan data/plan_2026.csv
  python tools/board-pack/build_board_pack.py --sample          # deck MẪU từ dữ liệu tổng hợp
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from . import HERE, REPO
from .commentary import Rules

AFI_DATA = REPO / "alta-finance-intelligence" / "data"


def main(argv: list[str] | None = None, data_default: Path | None = None) -> int:
    ap = argparse.ArgumentParser(prog="boardpack", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--month", help="kỳ báo cáo YYYY-MM (mặc định 2026-10 với --sample)")
    ap.add_argument("--mode", choices=["month", "ytd"], default="month", help="tháng hoặc lũy kế từ đầu năm")
    ap.add_argument("--data", type=Path, default=data_default or AFI_DATA, help="thư mục data của alta-finance-intelligence")
    ap.add_argument("--plan", type=Path, help="CSV kế hoạch: company, month, line, amount (VND)")
    ap.add_argument("--out", type=Path, help="file .pptx đầu ra")
    ap.add_argument("--threshold-pct", type=float, default=0.10, help="ngưỡng % giải trình (mặc định 0.10)")
    ap.add_argument("--threshold-amount", type=float, default=500e6, help="ngưỡng tuyệt đối VND (mặc định 500.000.000)")
    ap.add_argument("--sample", action="store_true", help="dựng warehouse tổng hợp + kế hoạch mẫu, đánh dấu DỮ LIỆU MẪU")
    a = ap.parse_args(argv)

    from afi.models.warehouse import Warehouse  # noqa: PLC0415

    from .deck import build_deck  # noqa: PLC0415
    from .facts import Facts  # noqa: PLC0415

    rules = Rules(a.threshold_pct, a.threshold_amount)
    if a.sample:
        from .sample import build_warehouse, write_plan  # noqa: PLC0415
        month = a.month or "2026-10"
        work = Path(tempfile.mkdtemp(prefix="boardpack-sample-"))
        approve = [(c, f"2026-{i:02d}") for c in ("ALTA", "APL") for i in range(1, 11)] + [("AME", f"2026-{i:02d}") for i in range(1, 10)]
        wh = build_warehouse(work, approve=approve)
        plan = a.plan or write_plan(Facts(wh), int(month[:4]), HERE.parent / "sample" / f"ke_hoach_mau_{month[:4]}.csv")
        facts = Facts(wh, plan)
    else:
        if not a.month:
            ap.error("--month là bắt buộc")
        month = a.month
        wh = Warehouse(a.data)
        facts = Facts(wh, a.plan)
    tag = "" if a.mode == "month" else "_LK"
    out = a.out or (HERE.parent / "output" / f"BoardPack_{month}{tag}{'_MAU' if a.sample else ''}.pptx")
    path, deck = build_deck(facts, month, a.mode, out, rules, sample=a.sample)
    st = deck.ST[None]
    print(f"{path} · {len(deck.prs.slides)} trang · trạng thái số liệu: {st.label} · {sum(len(v) for v in deck.VAR.values())} biến động vượt ngưỡng")
    return 0


if __name__ == "__main__":
    sys.exit(main())

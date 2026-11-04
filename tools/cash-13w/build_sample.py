"""Tạo dữ liệu MẪU (tổng hợp) cho cash13w.html và nhúng vào trang.

  python tools/cash-13w/build_sample.py [--start 2026-11-02]

Chạy đúng đường thật: sinh NKC kiểu FAST → afi ingest → dự báo tuần trước (lưu phiên bản) → dự báo tuần này
(so sánh với phiên bản trước). Kết quả: sample_cash13w.json (để thử kéo thả) và dữ liệu nhúng trong cash13w.html.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import tempfile
from pathlib import Path

from afi.forecasts import cash13w as cf
from afi.forecasts.cash13w_sample import write_sample
from afi.pipeline import Pipeline

HERE = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-11-02")
    a = ap.parse_args()
    start = dt.date.fromisoformat(a.start)
    prev = start - dt.timedelta(days=7)
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        s = write_sample(t / "sample", start)
        pl = Pipeline(t / "data")
        for g in s["gl"]:
            pl.ingest(g)
        prior = cf.build(s["inputs_prior"], prev, data=t / "data", created_at=dt.datetime.combine(prev, dt.time(8, 30)))
        cf.save_version(prior, t / "data")
        res = cf.build(s["inputs"], start, data=t / "data", created_at=dt.datetime.combine(start, dt.time(8, 30)))
    res["actual_rows"] = []  # lineage rows stay in Excel; keep the page light
    js = json.dumps(res, ensure_ascii=False, default=str, separators=(",", ":"))
    (HERE / "sample_cash13w.json").write_text(js, encoding="utf-8")
    page = HERE / "cash13w.html"
    html = page.read_text(encoding="utf-8")
    html = re.sub(r'(<script id="sample" type="application/json">)(.*?)(</script>)',
                  lambda m: m.group(1) + js.replace("</", "<\\/") + m.group(3), html, count=1, flags=re.S)
    page.write_text(html, encoding="utf-8")
    print(f"sample embedded: {len(js):,} bytes · {res['version_id']} · so với {res['comparison'].get('prior_version_id')}")


if __name__ == "__main__":
    main()

"""Tạo bản HTML đầy đủ v3 (mở trực tiếp bằng trình duyệt) từ dashboard/src/dashboard.html.
Bản v2 giữ nguyên ở dashboard/Alta_CFO_CEO_Dashboard_v2.html (nguồn: dashboard/src/dashboard_v2.html)."""
import pathlib
root = pathlib.Path(__file__).resolve().parent.parent
src = (root / "dashboard/src/dashboard.html").read_text(encoding="utf-8")
i = src.index("<header")
head, body = src[:i], src[i:]
out = ("<!doctype html>\n<html lang=\"vi\">\n<head>\n<meta charset=\"utf-8\">\n"
       "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
       "<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n"
       + head + "</head>\n<body>\n" + body + "\n</body>\n</html>\n")
dst = root / "dashboard/Alta_CFO_CEO_Dashboard_v3.html"
dst.write_text(out, encoding="utf-8")
print(dst, len(out))

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

# Bản ngoại tuyến: nhúng sẵn ECharts và SheetJS (dashboard/vendor/) để mở được khi không tải được CDN.
vend = root / "dashboard/vendor"
off = out
for url, fn in [("https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.1/echarts.min.js", "echarts-5.5.1.min.js"),
                ("https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js", "xlsx-0.18.5.full.min.js")]:
    tag = '<script src="%s"></script>' % url
    assert tag in off, tag
    lib = (vend / fn).read_text(encoding="utf-8").replace("</script", "<\\/script")
    off = off.replace(tag, "<script>/* %s (Apache-2.0, xem dashboard/vendor) */\n%s\n</script>" % (fn, lib))
dst2 = root / "dashboard/Alta_CFO_CEO_Dashboard_v3_offline.html"
dst2.write_text(off, encoding="utf-8")
print(dst2, len(off))

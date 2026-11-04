# Dòng tiền 13 tuần — trang xem (công cụ #3)

- `cash13w.html` — mở bằng Chrome/Edge (hoặc bản online riêng tư https://claude.ai/artifact/PL9kJr4Wx3SCPUqBjoPn72), kéo thả file `CF13W-….json` do `afi cash13w` xuất. File chỉ được đọc trong trình duyệt.
- Khi mở lần đầu trang hiện **dữ liệu mẫu tổng hợp** (có băng cảnh báo MẪU); nạp file thật sẽ thay thế.
- `sample_cash13w.json` — cùng dữ liệu mẫu, để thử kéo thả.
- `build_sample.py` — tạo lại dữ liệu mẫu qua đúng pipeline (sinh NKC giả lập → ingest → dự báo tuần trước → dự báo tuần này) và nhúng vào trang: `python tools/cash-13w/build_sample.py` (cần `pip install -e alta-finance-intelligence`).

Cách lập dự báo, mẫu CSV đầu vào và quy tắc: `alta-finance-intelligence/README.md` (mục "Dòng tiền 13 tuần") và `core/cash-13-week-treasury/SKILL.md`.

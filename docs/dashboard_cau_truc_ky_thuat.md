# Dashboard CFO · CEO: cấu trúc kỹ thuật

Tài liệu cho người sửa mã. Mô tả bản v3.3 (05/11/2026). Hướng dẫn dùng cho người đọc số: [`dashboard_huong_dan_su_dung.md`](dashboard_huong_dan_su_dung.md).

## 1. Tệp và cách dựng

| Tệp | Vai trò |
|---|---|
| `dashboard/src/dashboard.html` | **Mã nguồn duy nhất cần sửa.** Một file gồm HTML + CSS + JavaScript (khoảng 2.500 dòng, nhiều dòng dài). |
| `scripts/build_dashboard.py` | Dựng hai bản phát hành từ mã nguồn. Chạy: `python3 scripts/build_dashboard.py`. |
| `dashboard/Alta_CFO_CEO_Dashboard_v3.html` | Bản phát hành thường: thư viện tải từ CDN cdnjs; nếu không tải được thì dùng `vendor/` cạnh file. |
| `dashboard/Alta_CFO_CEO_Dashboard_v3_offline.html` | Bản phát hành ngoại tuyến: nhúng sẵn ECharts và SheetJS (khoảng 2 MB), mở được không cần mạng. |
| `dashboard/vendor/` | `echarts-5.5.1.min.js`, `xlsx-0.18.5.full.min.js` và giấy phép Apache-2.0 của hai thư viện. |
| `dashboard/src/dashboard_v2.html`, `dashboard/Alta_CFO_CEO_Dashboard_v2.html` | Bản v2 lưu trữ để so sánh. Không sửa. |

Quy trình sửa:
1. Sửa `dashboard/src/dashboard.html`.
2. Chạy `python3 scripts/build_dashboard.py`.
3. Mở `Alta_CFO_CEO_Dashboard_v3.html` bằng Chrome hoặc Edge, nạp thử thư mục FAST (mục 9).
4. Commit cả file nguồn lẫn hai bản phát hành.

Script dựng làm hai việc:
- Bọc phần đầu (trước `<header`) vào `<head>`, phần còn lại vào `<body>`, ghi ra bản thường.
- Thay hai thẻ `<script src="https://cdnjs…">` bằng nội dung thư viện trong `vendor/`, ghi ra bản offline. Thẻ thư viện Excel nhúng có `id="lib-xlsx"`; luồng nền đọc Excel lấy mã thư viện từ thẻ này.

Bản v3 trước đây được ghép từ nhiều mô-đun bằng một script vá tạm. Từ nay `dashboard/src/dashboard.html` là nguồn duy nhất, không còn bước ghép.

## 2. Bố cục file nguồn

Số dòng chỉ để tham khảo, sẽ lệch dần khi sửa. Hãy tìm theo **tên khối** (dòng chú thích `/* ==== tên */`) hoặc tên hàm.

| Vị trí | Nội dung |
|---|---|
| đầu file → ~dòng 120 | `<title>`, font Google, CSS. Màu khai báo bằng biến trên `:root`, có bộ màu tối. Lớp hay dùng: `.panel`, `.tile`, `.chip` (`st-good`, `st-warn`, `st-crit`), `.btn`, `.empty`, `.demo` (băng thông báo), `.tbl-wrap`, `.chart`, `.note`. |
| ~120–146 | `<header>`: chọn đơn vị (`#coSeg`), chọn tháng (`#selMonth`), chế độ kỳ (`#modeSeg`), ô “Loại trừ nội bộ” (`#chkElim`), nút “Lưu bản chia sẻ” (`#btnShare`); thanh trang (`nav.tabs`); `<main id="main">`; hộp truy xuất `#drill`; hai ô chọn file ẩn `#fileIn`, `#dirIn`. |
| ~142–144 | Thẻ thư viện CDN và đoạn dự phòng `vendor/`. |
| ~145–540 | `AltaModel`: mô hình chỉ số sản xuất, chép nguyên văn từ file “Tổng quan sản xuất – Alta Plastics”. Không sửa tay. |
| ~544 → hết | Script chính (`"use strict"`), chia khối như bảng dưới. |

### Các khối trong script chính

| Khối (tìm theo chú thích) | Nội dung chính |
|---|---|
| `hằng số` | `CO` (nhãn đơn vị), `COS` (mã ngắn ALTA/PLASTIC/MEDIA), `IC_DEFAULT` (MST nội bộ), `TYPES`, `ACC` (tên TK), `CASH`/`DEBT`/`INV`, `CF_CAT` (nhóm dòng tiền theo TK đối ứng), `PL` (công thức KQKD), `BAL` (công thức số dư) |
| `tiện ích` | `$`, `$$`, `esc`, `norm` (bỏ dấu), `fB`/`fN`/`fP` (định dạng số), `num` (đọc số Việt Nam), `ymd` (đọc ngày, kể cả số ngày Excel), `mAdd`/`mRange`/`mEnd`/`mLbl` (tháng dạng `YYYY-MM`), `toast`, `store` (localStorage, tiền tố `altadash:`) |
| `IndexedDB` | `IDB` (CSDL `alta-fast-dash-v3`): lưu các file đã nạp trong trình duyệt |
| `đọc file FAST` | Bộ đọc cũ v1/v2 (`parseSheet`, `detectType`…) cho file không phải mẫu FAST chuẩn, file kế hoạch |
| `trạng thái` | `S`: trạng thái toàn cục (mục 3) |
| `mô hình dữ liệu` | `build()`: dựng `S.D` từ `S.files` |
| `công thức` | `periodMonths`, `sumP`, `pl` (chỉ tiêu KQKD), `bal`/`bal1` (số dư), `cfSum`, `planV` |
| `truy xuất ngược` | `drillPL`, `drillBal`, `drillCF`, `openDrill`, `renderDrill` (hộp truy xuất chứng từ) |
| `biểu đồ` | `mk()`: tạo biểu đồ ECharts, gắn nút xuất CSV/Excel/PNG; `theme()`, `axX`, `axY` |
| `trang CEO`, `trang CFO`, `trang bán hàng` | `pageCEO`, `pageCFO`, `pageSales`, `plTable` |
| `trang dữ liệu` | `runChecks` (gộp mọi kiểm tra, có bộ nhớ đệm), `runChecksBase` (kiểm tra v2) |
| `trang quy trình` | `pageGuide` (trang “Quy trình” trong app) |
| `công nợ, TSCĐ, tồn kho (đợt 2)` | `plOK`, `debtData`, `pageDebt`, `pageFAold`, `pageStockOld`, `runChecksExt`, `fnMatrix`, `parseExt` |
| `dữ liệu mẫu bổ sung`, `dữ liệu mẫu` | Bộ sinh số mẫu của v2. **Không còn được gọi** (bản bàn giao không có số mẫu); giữ lại để tham khảo, có thể xóa. |
| `sản xuất Alta Plastics` | `readProdHtml`, `pageProd` (đọc file HTML sản xuất, dùng `AltaModel`) |
| `BỘ ĐỌC BÁO CÁO FAST` | `FAST_SPECS`, `FAST_TYPE_NAME`, `fastTitle`, `fastHeader`, `fastPeriod`, `parseFast`, `UNIT_MAP`, `ROLE` |
| `v3: nạp FAST…` | `PT2`, `DATA_TYPES`, `buildFast`, `readFile`, `loadFiles`, `runChecksFastU` (kiểm tra đối chiếu của một đơn vị), `metricRowsU` (bảng chỉ tiêu một đơn vị) |
| `v3: trang Dữ liệu nguồn…` | `USES`, `fastMatrix`, `pageData`, `pageRecon`, `pageOrders`, `debtExtra`, `pageFA`, `stockExtra`, `pageStock`, `markTiles` |
| `v4: đơn vị…` | `UNIT_CODES`, `unitTokens`, `normFilters`, `fromFilters`, `readMetaJson`, `applyMeta`, `scopeKey`, `dupMark`, `usable`, `fileStatus`, `fileCat`, `groupLbl`, `consOK`, `detailUnit`, `unitSwitch`, `withUnit`, `groupBanner`, `STATE_TYPES`, `unitStatePanel`, `stagePanel`/`stageFiles`, `addFiles`, `runChecksFast`, `metricRows`, `issueRows`, `exportRows`, `kqvvSection`, `covOK`, `ttmMiss`, `snapL`, `repPer`, `suppBox`, `scopeSheet`, `libBanner` |
| `v3.3: lưu bản chia sẻ…` | `saveFile`, `download`, `exportBook`, `chartTools`/`chartTable`/`chartPNG`, `exportDrill`, `buildSnapshotHTML`/`shareSnapshot`/`loadSnapshot`/`applySnapshot`/`roBanner`, `xlsxWorker`/`readSheets` |
| `điều khiển` | `controls`, `syncControls`, `PAGES` (bảng trang ↔ hàm), `render`, `tileDrill`, `refresh` |
| `khởi động` | `boot()`: đọc bản chia sẻ nhúng (nếu có) hoặc IndexedDB, rồi `build()` và `render()` |

Script chạy ở chế độ `"use strict"`, tất cả nằm trong một phạm vi chung. **Không được khai báo trùng tên hàm hoặc hằng**: tên `const` trùng sẽ làm cả trang không chạy.

## 3. Luồng dữ liệu

```
Chọn file / thư mục ─► addFiles ─► (có đường dẫn thư mục và >3 file) stageFiles: rà soát ─► bấm “Nạp”
                                  └► loadFiles ─► readFile (từng file)
                                        ├─ .json  → readMetaJson → type 'meta' | 'supp' | 'ref'
                                        ├─ .html  → readProdHtml (file sản xuất) | 'ref'
                                        └─ .xlsx  → readSheets (luồng nền) → parseFast (mẫu FAST) | parseSheet (mẫu cũ)
                                     ─► S.files.push(f); IDB.put(f)
refresh() = build() + render()
build():  applyMeta()  → gắn đơn vị, bộ lọc, loại yếu tố, chiều tăng/giảm, metadata chuẩn (f.meta)
          dupMark()    → đánh dấu bản trùng
          files = S.files.filter(usable)
          win          → chọn file “thắng” cho mỗi khóa nguồn (file nạp sau thắng)
          G  (dòng NKC), SL (bảng kê bán hàng), CD (CĐPS), PB/IV/ST/FA (công nợ, hóa đơn, tồn kho, TSCĐ)
          byCM, mvCM, DA, CF, LI… (tổng hợp theo đơn vị|tháng|TK)
          S.D.F  = buildFast(files)                 (mọi đơn vị, dùng cho bảng tra có khóa đơn vị)
          S.D.FU = {0,1,2: buildFast(files của đơn vị)}  (sổ chi tiết, BCTC FAST, TSCĐ, kho… theo đơn vị)
render(): C1 = detailUnit(); gọi PAGES[trang]() → [html, after]; gắn sự kiện; markTiles, groupBanner, libBanner, roBanner
```

### Đối tượng file (`S.files[i]`)

Do `parseFast` và `applyMeta` tạo ra. Lưu nguyên vào IndexedDB, trừ trường `aoa`.

| Trường | Ý nghĩa |
|---|---|
| `id`, `added`, `name`, `path`, `sheet`, `sha`, `chash` | Định danh. `sha` = SHA-256 cả file; `chash` = SHA-256 nội dung ô của sheet. |
| `type` | Loại nguồn: `gl, cdps, ledger, arp, app, ari, api, aga, agp, fareg, dep, fachg, ccdc, ccdcm, stock, pnk, pxk, isM, is, bs, cfs, pcost, so, po, pc154, nvl, kqvv, acclist, sales, purch` (mẫu FAST); `plan, prod`; `meta, supp, ref` (kê khai, tham khảo) |
| `fast`, `title`, `subtitle`, `hdrRow`, `stats` | Tiêu đề báo cáo; dòng tên cột; đếm dòng (`raw, data, total, group, blank, header, control`). |
| `rows`, `n` | Dòng dữ liệu chuẩn hóa, mỗi dòng có `r` = số dòng Excel gốc. |
| `period` [`YYYY-MM`,`YYYY-MM`], `asof`, `acc`, `scope` | Kỳ, ngày chốt, TK, phạm vi (`TK131`, `yt01`, `chieu:tang`, `kho:*;dl:*`…). |
| `c`, `unit`, `unitBasis`, `unitPending`, `unitConflict`, `unitOK`, `cManual` | Đơn vị (0 ALTA, 1 PLASTIC, 2 MEDIA, −1 chưa rõ) và căn cứ. |
| `factor`, `assetDir`, `meta` | Loại yếu tố, chiều tăng/giảm, metadata chuẩn (schema mục 5). |
| `dupOf`, `on`, `err`, `pending`, `warn` | Bản trùng của file nào; bật/tắt; lỗi; chưa hỗ trợ; cảnh báo. |

### Trạng thái toàn cục `S`

| Trường | Ý nghĩa |
|---|---|
| `S.files` | Mọi file đã nạp. |
| `S.D` | Mô hình dựng bởi `build()`. Chỉ đọc khi vẽ trang. |
| `S.f` | Bộ chọn: `co` (−1 các đơn vị, 0/1/2), `m` (tháng `YYYY-MM`), `mode` (`month`/`ytd`/`ltm`), `elim`, `side`, `du`… |
| `S.ic` | MST nội bộ → đơn vị. |
| `S.stage`, `S.progress`, `S.pending` | Bước rà soát và tiến độ nạp. |
| `S.readonly`, `S.snap` | Đang mở bản chia sẻ. |
| `S.D._chk` | Bộ nhớ đệm kết quả `runChecks()`; xóa mỗi khi `build()`. |

Đơn vị đi qua mã nguồn bằng số: `c` 0/1/2. Tên mã lấy qua `ucode(c)`, nhãn qua `CO[c]`. Khóa tổng hợp có dạng `c|YYYY-MM|TK` hoặc `c|YYYY-MM`.

## 4. Quy tắc nghiệp vụ nằm trong mã

| Quy tắc | Vị trí |
|---|---|
| KQKD lấy từ NKC, loại bút toán có TK hoặc TK đối ứng 911 (`x.k`) | `build()`, `PL`, `sumP` |
| TK đối ứng NKC lấy theo cặp dòng Nợ → Có liền kề trong mỗi chứng từ; không tách được cặp thì để trống và gắn `mc` | `parseFast` case `gl` |
| Khấu hao: ưu tiên Bảng tính khấu hao nhiều kỳ (`S.D.F.DEPM`), nếu không có thì dùng Có 214 đối ứng 6xx/154/632; không dùng biến động ròng 214 | `sumP` (cờ `da`), `drillPL`, `plOK` |
| EBITDA = LNTT + lãi vay + khấu hao; CCDC không cộng lại | `PL.ebitda` |
| Kỳ phải đủ tháng: thiếu tháng thì chỉ tiêu báo “Chưa đủ dữ liệu” (12T/LTM) | `covOK`, `plOK`, `ttmMiss` |
| Sổ chi tiết, KQKD/CĐKT/LCTT FAST, sổ nhiều TK: chỉ dùng đối chiếu, không cộng vào chỉ tiêu | `buildFast` (đưa vào `F`, không vào `G`), `runChecksFastU` |
| Dư Nợ, dư Có công nợ tách riêng theo đối tượng | `debtExtra`, `metricRowsU` |
| Tuổi nợ theo nhóm của báo cáo FAST, ngày chốt của báo cáo (không dùng ngày hôm nay) | `debtExtra`, `debtData` (`x.asof`) |
| Đơn vị chỉ xác nhận khi có căn cứ mạnh (kê khai, bộ lọc `ma_dvcs`, cột Đơn vị); mâu thuẫn thì chờ xác nhận; `ALTA_` đứng trước PLASTIC/MEDIA là tiền tố tập đoàn | `applyMeta`, `unitTokens` |
| Bản trùng: cùng `scopeKey` + cùng `chash` | `dupMark` |
| “Hợp nhất” chỉ khi đủ 3 đơn vị và đã tick xác nhận loại trừ (`store elimOK`); nếu không thì là “Cộng gộp … (chưa phải hợp nhất)” và không trừ nội bộ | `consOK`, `groupLbl`, `syncControls` |
| Ba trạng thái nguồn: chưa xuất/chưa nạp · đã xuất, trống · có dữ liệu | `cellState`, `fileStatus` |
| Dòng tiền trực tiếp: TK tiền phân nhóm theo TK đối ứng trong `CF_CAT`; không khớp nhóm nào thì vào “chưa phân loại” | `cfCat`, `CF_CAT` |

## 5. Kê khai nguồn (metadata)

`readMetaJson` nhận các dạng sau:

| Dạng file JSON | Kết quả |
|---|---|
| Mảng bản ghi có `file` (`file_inventory.json`, `download_manifest.json`) | `type:'meta'`, `recs` |
| Đối tượng có `files`, `media_jobs`, `jobs`, `items`, `records` | `recs` |
| Đối tượng có `exports` (`audit_catalog.json`, `report_catalog.json`) | `exports` (bộ lọc FAST theo mã báo cáo) |
| Đối tượng có `catalog[].downloads` | `catalog` (mã báo cáo → tên file) |
| Mảng `{label,url,filters}` không có `file` (`media_jobs.json`) | `exports` |
| Mảng `{url,filters,result}` (`supplemental_checks.json`) | `type:'supp'` (báo cáo đã thử nhưng trống) |
| Khác | `type:'ref'` |

`applyMeta` gắn kê khai theo **thư mục gốc**, tức thư mục chứa file JSON. File Excel nằm trong thư mục con của thư mục đó dùng kê khai đó. Bộ lọc FAST (`ctl00_…_form_tk` → `tk`) được chuẩn hóa bằng `normFilters` và đọc nghĩa bằng `fromFilters`:

| Bộ lọc | Trường |
|---|---|
| `ma_dvcs` | đơn vị |
| `tk` | account |
| `tu_ngay`/`den_ngay`, `tu_ky`/`tu_nam`… | period_start, period_end |
| `date`, `ky`+`nam` | as_of_date |
| `ngay_tt` | payment_cutoff |
| `ma_loai` | cost_factor |
| `type` 1/2 | chiều tăng/giảm |
| `ma_kho`, `loai_du_lieu` | kho, loại dữ liệu |

Kết quả nằm ở `f.meta` theo schema: `source_id, unit_code, report_type, period_start, period_end, as_of_date, payment_cutoff, account, cost_factor, asset_direction, kho, data_kind, filters, filters_basis, exported_at, source_file, sheet, raw_file_sha256, cell_content_sha256, unit_basis, validation_status, empty_by_filter`.

## 6. Việc sửa thường gặp

### Thêm một mẫu báo cáo FAST

1. Thêm dòng vào `FAST_SPECS`:
   `{id:'xyz', t:/^tieu de khong dau$/, h:['ten cot 1','ten cot 2'], name:'Tên hiển thị'}`
   - `t` so với tiêu đề đã chuẩn hóa: bỏ dấu, chữ thường, chỉ còn chữ, số và dấu cách (hàm `norm`).
   - `h` là các tên cột bắt buộc, cũng đã chuẩn hóa.
   - Mẫu có tiêu đề dễ trùng thì đặt lên đầu mảng.
2. Thêm `case 'xyz':{…}` trong `parseFast`.
   - Duyệt từ `start`; dùng `col('ten cot')`, `s(r,i)`, `n(r,i)`, `d(r,i)`.
   - Đếm `st.data / total / group / blank`, đẩy dòng vào `out.rows`; mỗi dòng phải có `r:i+1`.
   - Bỏ dòng tổng bằng `hasTot(r)`.
3. Khai báo tên và vai trò: `FAST_TYPE_NAME`, `ROLE`, `USES`.
4. Thêm `id` vào `PT2` nếu nguồn có phạm vi theo kỳ hoặc snapshot (gần như luôn cần). Thêm vào `STATE_TYPES` để hiện trong bảng trạng thái.
5. Muốn dùng số trong trang: thêm `case 'xyz'` trong `buildFast` để đưa vào `F.<TÊN>`, rồi đọc ở trang qua `S.D.FU[C1].<TÊN>`.
6. Chạy thử với file thật. Bảng “Kiểm tra đầu vào từng file” phải hiện đúng loại báo cáo và số dòng hợp lệ.

### Thêm một kiểm tra đối chiếu

Thêm vào `runChecksFastU(C)`. Tham số `C` là đơn vị; `F = D.FU[C]`; hàm `lf(C, ['211'], 'dn1')` lấy số dư lá trên CĐPS.

```js
out.push(chk({grp:'Tài sản', n:'Tên kiểm tra', s:'phạm vi', ok:Math.abs(a-b)<1000, warn:true,
  d:'Diễn giải có số', table:{h:[…],rows:[…]}, drill:()=>openDrill({...})}))
```

- `ok` = đạt.
- `warn:true` = “Cần xem” khi không đạt; không có `warn` thì là “Không đạt”.
- `table` hiện bảng chi tiết; `drill` cho phép bấm để xem chứng từ.
- Không viết kiểm tra để “làm xanh”: chênh lệch chưa có bằng chứng phải giữ là không đạt.

### Thêm một chỉ tiêu KQKD

Thêm vào `PL`: `{n:'Tên', f:'Công thức hiển thị', p:[[['TK…'],'cn'|'nc', dấu, cờ?]], e:0}`.
- `cn` = Có − Nợ; `nc` = Nợ − Có.
- Cờ `li` = lãi vay; `da` = khấu hao.
- Muốn có trong file xuất: thêm vào danh sách chỉ tiêu trong `metricRowsU`.

### Thêm một trang

1. Viết `function pageXyz(){ … return [html, ()=>{ /* gắn sự kiện */ }] }`.
2. Thêm vào `PAGES` (bọc `withUnit(...)` nếu trang xem theo từng đơn vị).
3. Thêm thẻ `<a href="#xyz">` vào `nav.tabs`.
4. Biểu đồ tạo bằng `mk(el, T=>({...option}), onClick)`: nút xuất CSV/Excel/PNG tự gắn.
5. Bảng có số thì cho truy xuất bằng `openDrill({title, formula, rows, value, cols})`; mỗi dòng cần `v` (giá trị), `r` (dòng Excel), `f` (id file).

### Thêm đơn vị mới

1. Thêm mã vào `UNIT_MAP` và `UNIT_CODES`; thêm nhãn vào `CO` và `COS`.
2. Sửa các vòng `[0,1,2]` (tìm `[0,1,2]` trong file).
3. Sửa regex mã trong `unitTokens`.

### Đổi nhóm dòng tiền

Sửa `CF_CAT`: `[tên, nhóm HĐKD|HĐĐT|HĐTC|Nội bộ, [tiền tố TK đối ứng]]`. Tiền tố dài nhất thắng.

## 7. Các bẫy đã gặp

| Bẫy | Cách tránh |
|---|---|
| Chuỗi `</script>` trong mã JavaScript nội tuyến kết thúc thẻ script sớm, cả trang chết | Viết `<\/script>` trong chuỗi |
| Khai báo `const` hoặc `function` trùng tên | Tìm tên trước khi thêm |
| Biểu thức chính quy xử lý chính mã HTML của trang (khi tạo bản chia sẻ) có thể khớp nhầm vào mã nguồn | Dùng DOM (`cloneNode`, `querySelector`), không dùng biểu thức chuỗi trên toàn trang |
| Tên phông có dấu ngoặc kép làm SVG của ECharts không hợp lệ khi đổi sang PNG | `chartPNG` đã làm sạch; giữ nguyên |
| Playwright không chuyển được file có tên tiếng Việt qua đường dẫn | Khi kiểm thử tự động, nạp file bằng `buffer` kèm tên |
| Đổi tên CSDL IndexedDB làm người dùng mất dữ liệu đã nạp | Giữ `alta-fast-dash-v3`; đổi khi cố ý tách phiên bản |
| Nút lưu/xuất trên link claude.ai | Phải đi qua `saveFile` (dùng quyền `downloads`); không tạo `<a download>` trực tiếp |
| Thư viện không tải được | `mk()` hiện thông báo thay biểu đồ; `libBanner()` báo thiếu thư viện; app vẫn chạy |

## 8. Bản chia sẻ

`shareSnapshot()` thực hiện:
1. Lấy `S.files` theo đơn vị đang chọn (`shareFiles`), bỏ file tắt.
2. Thêm cài đặt (MST nội bộ, TK tồn kho, xác nhận loại trừ, bộ chọn).
3. Nén gzip (`CompressionStream`), mã hóa base64.
4. Chèn vào bản sao trang (`SELF_HTML`, chụp lúc khởi động) dưới dạng `<script type="application/x-alta-snapshot" id="snapData">`.

Khi mở bản chia sẻ, `boot()` gọi `loadSnapshot()` rồi `applySnapshot()`:
- bật `S.readonly`;
- vô hiệu `IDB.put/del/clear` (không ghi vào máy người nhận);
- cài đặt chỉ giữ trong bộ nhớ;
- ẩn khu nạp, xóa và sửa bằng lớp CSS `body.ro`.

## 9. Kiểm thử sau khi sửa

Không có bộ kiểm thử tự động trong repo. Trước khi phát hành, tối thiểu làm theo danh sách sau với hai thư mục FAST PLASTIC và MEDIA:

1. Mở bản thường. Console (F12) không có lỗi đỏ.
2. Chọn cả thư mục → bước rà soát hiện đúng đơn vị, không mâu thuẫn → Nạp.
3. Trang Dữ liệu nguồn: 96 Excel; PLASTIC 44 dùng + 2 trùng + 1 trống; MEDIA 38 dùng + 11 trống; 0 chờ.
4. Số đối chứng 9T/2026 (NKC, loại 911):

   | | PLASTIC | MEDIA |
   |---|---:|---:|
   | Doanh thu thuần | 255.734.182.421 | 65.291.680.758 |
   | LNTT | 37.120.651.173 | 2.427.885.080 |
   | EBITDA | 45.801.117.006 | 15.998.475.652 |

5. Nạp theo thứ tự ngược lại hoặc nạp lại cùng thư mục: số không đổi, số file không tăng.
6. Đổi đơn vị, tháng, chế độ kỳ: số và nhãn đổi đúng; chế độ “12 tháng” với dữ liệu 9 tháng báo thiếu tháng.
7. Bấm một số, một cột biểu đồ: hộp truy xuất mở; dòng “Tổng các dòng” khớp số hiển thị.
8. Xuất CSV/Excel/PNG một biểu đồ; Tải Excel chỉ tiêu; Lưu bản chia sẻ rồi mở bản đó khi tắt mạng (lưu từ bản offline).
9. Mở bản offline khi tắt mạng: nạp được Excel, có biểu đồ.

Kết quả lần kiểm thử gần nhất: [`fast_nap_thu_plastic_media_2026-11-05.md`](fast_nap_thu_plastic_media_2026-11-05.md).

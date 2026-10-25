# Paper trading nối vào nghiệp vụ chính: tóm tắt và đề xuất pha 2 (gửi BE1)

**Người viết:** BE3 · **Ngày:** 2026-10-25 · **Trạng thái:** để bàn, chưa chốt pha 2
**Liên quan:** D-117 (đã ghi trong CURRENT_STATE), kế hoạch chi tiết pha 1: `docs/design/paper-core-integration-plan.md`

---

## 1. Vì sao làm

Trước đây (Q-T1, V21), 12 bảng `paper_*` đứng riêng hẳn: mọi dòng treo dưới `paper_account`, không cột nào trỏ tới `trading_plan`. Hệ quả:

- Trên ERD, paper là một hòn đảo, không nối vào plan, journal hay dashboard.
- Có hai nơi cùng làm một việc:
  - **Khớp lệnh:** `trading/matching/MatchingEngine` và engine của `paper`.
  - **Watermark:** `matching_watermark` và `paper_matching_watermark`.
  - **Funding:** `FundingCalculator` (T-045) và bảng `paper_funding_payment`.
  - **Kết quả giao dịch:** `trading_journal` và `paper_position`.

## 2. Pha 1 đã làm (BE3, chưa push)

**Không đụng một dòng nào trong package `trading`.** Engine của plan, TP-A, T-045 giữ nguyên.

| Trước | Sau (V34) |
|---|---|
| 12 bảng `paper_*` | 6 bảng nghiệp vụ + 1 bảng kỹ thuật, tất cả theo `user_id` |
| `paper_account` | bỏ; tài khoản "mở" khi đã có dòng INITIAL_GRANT trên ledger |
| `paper_transfer` | bỏ; mỗi lần chuyển là 2 dòng ledger cùng `ref_id`, có `client_transfer_id` |
| `paper_position`, `paper_funding_payment`, `paper_futures_setting` | xóa: chưa có code ghi; Futures giả lập = plan + journal + `funding_rate_history` |
| `paper_balance`, `paper_ledger_entry` | `wallet_balance`, `wallet_ledger_entry` |
| `paper_order_list`, `paper_order`, `paper_fill` | `order_list`, `trade_order` (**thêm `plan_id` → `trading_plan`, nullable**), `order_fill` |
| `paper_equity_snapshot` | `equity_snapshot` |
| `paper_matching_watermark` | `order_matching_watermark` (vẫn tách khỏi `matching_watermark`) |

**An toàn:**
- V34 chạy trong một transaction, kiểm tra dữ liệu trước và sau; sai thì rollback và báo lý do.
- Dữ liệu gốc giữ lại trong `legacy_paper_account`, `legacy_paper_transfer`, xóa ở V35 sau khoảng 1 tuần.

**Kiểm thử:**
- `mvnw clean verify` 3703/3703, chạy 2 lần.
- Migration chạy trên bản sao DB dev thật: số dư 36/36 dòng khớp; khớp lệnh, hủy lệnh, restart replay đều đúng.

**Ảnh hưởng tới BE1:**
- Code `trading` không đổi. Có thêm test `PaperTradingBoundaryTest`: `trading` và `paper` không được phụ thuộc nhau, và chỉ `paper` được nhắc tên bảng ví/lệnh. Sang pha 2 thì nới luật này theo thiết kế chốt.
- Lúc ghép `feat/admin-console` với V32, 5 test admin chèn `trading_plan` thiếu `analysis_timeframe` / `fill_liquidity`. Đã sửa phía admin, không sửa V32.

**Thứ tự merge:**
1. `feat/admin-console` (V33, kèm fix test).
2. FE `refactor/paper-account-shape`: chạy được với cả BE cũ lẫn mới.
3. BE `refactor/paper-into-core-schema` (V34), rebase lên develop. Nếu V34 đã có người dùng thì đổi số.

## 3. Pha 2: việc cần bàn với BE1

**Mục tiêu:** chỉ còn một engine khớp lệnh. Plan khi kích hoạt sẽ đặt lệnh thật trong hệ thống giả lập (`trade_order.plan_id`), kết quả đổ về `trading_journal`, tiền đi qua ví và ledger.

### 3.1 Ba phương án

| | A. Plan đặt lệnh paper (một engine) | B. Engine plan giữ nguyên, ghi sang bảng lệnh | C. Giữ hai engine, chỉ nối dữ liệu |
|---|---|---|---|
| Cách làm | Kích hoạt plan → tạo OTOCO: entry + OCO TP/SL trong `trade_order`; engine paper khớp; fill đóng thì `IJournalWriter` ghi journal | `MatchingEngine` vẫn khớp plan; mỗi lần khớp ghi thêm `trade_order` + `order_fill` qua một port của `paper` | Không đổi engine; journal và dashboard đọc thêm `order_fill` |
| Engine | 1 | 2 (một engine ghi bảng của module kia qua port) | 2 |
| Ví / vốn | Plan khóa tiền trong ví (`locked_amount`) như Binance | Phải tự trừ ví khi plan khớp | Plan không đụng ví |
| Futures | Engine paper phải có Futures: đòn bẩy, margin, liquidation theo mark, funding | Engine plan đã có (T-044, T-045) | Như hiện tại |
| Công sức | Lớn nhất | Vừa | Nhỏ |
| Rủi ro với code BE1 | Cao: thay `MatchingEngine` | Thấp | Gần như không |

**Đề xuất của BE3:** làm theo bước, mỗi bước merge được riêng.
1. **B cho Spot** sau T-048: plan Spot khớp thì ghi `trade_order`/`order_fill` có `plan_id` và trừ ví. Ví, lịch sử lệnh, PnL và journal dùng chung một nguồn, không đụng luật khớp của BE1.
2. **A cho Spot** khi engine paper đã đáp ứng được BR-33/BR-35 (mục 3.2). Lúc đó bỏ phần Spot của `MatchingEngine`.
3. **Futures** để cuối: hoặc giữ engine plan cho Futures (B), hoặc viết Futures cho engine paper (A). Quyết theo thời gian còn lại của capstone.

### 3.2 Khác biệt luật khớp phải chốt nếu chọn A

| Chủ đề | Engine plan (BE1) | Engine paper | Cần chốt |
|---|---|---|---|
| Nguồn giá | Nến 1 phút (range), last/mark | `@aggTrade` từng giao dịch + depth20 (VWAP), nến 1m làm dự phòng | Plan dùng nguồn nào; replay có ra cùng kết quả không |
| SL và TP chạm cùng nến | SL trước (BR-35) | OCO: giao dịch nào tới trước thì khớp trước | Giữ BR-35 cho plan? |
| Gap qua giá | Khớp tại giá mở nến (T-044) | Stop khớp tại giá trigger hoặc giá mở khi replay | Thống nhất một luật |
| Phí maker/taker | Theo liquidity role (TP-0 E1) | Theo cách lệnh vào sổ | Ánh xạ `fill_liquidity` |
| Slippage | TP-0 E2/E3 | Theo depth thật | Bỏ slippage mô phỏng khi có depth? |
| Entry STOP, invalidation, deviation | TP-A, TP-B, TP-C | Có STOP_LOSS_LIMIT/STOP_MARKET, không có invalidation | Invalidation thành hủy lệnh chờ |
| Liquidation | Theo mark price (BR-26..28, D-97) | Chưa có (Spot) | Chỉ áp cho Futures |
| Hết hạn plan (NSF-09) | Engine plan | Lệnh có `EXPIRED` | Job hết hạn hủy `trade_order` của plan |

### 3.3 Câu hỏi cho BE1

1. TP-0, TP-B, TP-C, T-046 đang tới đâu? Pha 2 nên bắt đầu sau mốc nào để không giẫm chân nhau?
2. BR-33/BR-35 có bắt buộc giữ y nguyên cho plan không, hay được phép theo luật engine paper (giống Binance hơn)?
3. Vốn của plan có lấy từ ví giả lập không? Nếu có: kích hoạt plan thì khóa tiền, thiếu tiền thì từ chối bằng MSG nào?
4. Journal (T-048, `IJournalWriter`) nhận sự kiện từ đâu: `PositionClosed` của engine plan, hay fill đóng của `trade_order`? Có cần thêm `trading_journal.entry_order_id` / `exit_order_id` không?
5. Gộp `matching_watermark` và `order_matching_watermark`: thêm cột `engine` hay để mỗi engine một bảng tới khi chỉ còn một engine?
6. Futures cho tài khoản giả lập: có nằm trong phạm vi capstone không? Form đăng ký chỉ yêu cầu plan, quản lý rủi ro và journal giả lập.

## 4. Bước tiếp theo đề xuất

1. BE1 đọc file này, trả lời mục 3.3. Họp ngắn 30 phút chốt phương án và thứ tự.
2. Ghi quyết định pha 2 thành D-117, thêm task vào CURRENT_STATE (gợi ý: PCI-2a Spot ghi lệnh, PCI-2b engine chung Spot, PCI-2c Futures).
3. Leader xác nhận D-117 và cập nhật SRS/ERD theo kết quả.

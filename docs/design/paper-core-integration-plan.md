# Kế hoạch: nối paper trading vào nghiệp vụ chính (PCI)

**Trạng thái:** ĐÃ THỰC THI 2026-10-24 (BE3) — BE `refactor/paper-into-core-schema` (`e9ea8d4`, `76ea987`, trên `feat/admin-console` (`e9ea8d4` = admin + develop `f47ca1b` + fix test)), FE `refactor/paper-account-shape` (`8557fb6`); chưa push. Thứ tự merge: admin-console → FE → BE (FE đọc được cả BE cũ lẫn mới)
**Phạm vi đã chốt:** tái cấu trúc DB + nối khóa; giữ 2 engine khớp lệnh và hành vi như cũ (gộp engine là pha 2, làm cùng BE1)

---

## 1. Hiện trạng (develop `f47ca1b`)

- 55 bảng: 43 bảng nghiệp vụ/kỹ thuật + 12 bảng `paper_*` (V21). Theo V21 (Q-T1), không cột nào của paper trỏ tới `trading_plan`; paper chỉ nối `user_account`, `coin`, `crypto_pair` qua `paper_account`.
- Paper mới chạy Spot. 3 bảng Futures **không có dòng code nào dùng**: `paper_position`, `paper_funding_payment`, `paper_futures_setting` (chỉ test schema nhắc tới).
- `paper_account` là bảng 1–1 với user, ngoài khóa chỉ có `position_mode` (khái niệm của Futures). Có 14 file service dùng `PaperAccount` làm gốc.
- `paper_transfer`: mỗi lần chuyển tiền đã được ghi thành 2 dòng ledger `TRANSFER` (ref = transfer_id), bảng này chỉ thêm `client_transfer_id` và from/to.
- FE gọi đủ các API `/api/v1/paper/*` (account, wallets, transfers, ledger, orders, order-lists, fills, spot/pnl, equity); `PaperAccount` của FE có `positionMode`.
- Engine của plan (`trading/`) do BE1 đang phát triển tiếp (TP-0, TP-B, TP-C), T-046 và T-048 (journal) chưa làm.
- `feat/admin-console` (của BE3, chưa merge) đã chiếm **V33** và sửa 7 file paper (D-115).

## 2. Mô hình đích

### 2.1 Quyết định

| # | Quyết định | Lý do |
|---|---|---|
| P1 | Giữ 2 engine; DB và khóa nối ngay, gộp engine ở pha 2 | Không viết lại code BE1 đang làm |
| P2 | Vẫn cho đặt lệnh tay (`plan_id` nullable), giữ `order_list` cho OCO/OTO/OTOCO tay | Màn hình Spot của FE và phần làm cho giống Binance (#65) vẫn chạy |
| P3 | Bỏ 3 bảng Futures-paper: Futures giả lập = `trading_plan` + `trading_journal` + `funding_rate_history` | Không có code, không có dữ liệu; tránh 2 nơi cùng lưu một vị thế |
| P4 | Bỏ `paper_account`: mọi bảng dùng thẳng `user_id`; `position_mode` bỏ theo Futures | Bảng 1–1 dư thừa |
| P5 | Gộp `paper_transfer` vào ledger: thêm `client_transfer_id` vào dòng ledger | Ledger đã chứa đủ dữ liệu chuyển tiền |
| P6 | Đổi tên bảng bỏ tiền tố `paper_`; giữ package Java `paper` và đường dẫn `/api/v1/paper` | Bảng thuộc mô hình chung; API giữ nguyên nên FE chỉ sửa ít |
| P7 | Watermark của paper giữ bảng riêng (kỹ thuật, như `binance_ban`), đổi tên; gộp với `matching_watermark` ở pha 2 | Gộp ngay sẽ đụng phần replay BE1 đang sửa (TP-B) |

### 2.2 Bảng sau khi sửa

| Bảng cũ | Bảng mới | Ghi chú |
|---|---|---|
| `paper_balance` | `wallet_balance` | `account_id` → `user_id` |
| `paper_ledger_entry` | `wallet_ledger_entry` | `user_id`; thêm `client_transfer_id`; ref `ACCOUNT` → `USER` |
| `paper_order_list` | `order_list` | `user_id` |
| `paper_order` | `trade_order` | `user_id`; thêm `plan_id` → `trading_plan` (nullable) |
| `paper_fill` | `order_fill` | `user_id` |
| `paper_equity_snapshot` | `equity_snapshot` | `user_id` |
| `paper_matching_watermark` | `order_matching_watermark` | kỹ thuật, không nằm trong ERD conceptual |
| `paper_account` | — | đổi tên thành `legacy_paper_account` (lưới an toàn, §5) |
| `paper_transfer` | — | đổi tên thành `legacy_paper_transfer` (lưới an toàn) |
| `paper_position`, `paper_funding_payment`, `paper_futures_setting` | — | xóa (migration kiểm tra bảng rỗng trước khi xóa) |

**Số bảng:** 12 → 7 (6 nghiệp vụ + 1 kỹ thuật). Toàn DB: 55 → 50, cộng 2 bảng `legacy_*` cho tới khi xóa ở V35 (§5.3).

### 2.3 Quan hệ conceptual

```
user_account 1──n wallet_balance ──n─1 coin
user_account 1──n wallet_ledger_entry (sổ cái; tổng các dòng = số dư)
user_account 1──n trading_plan 1──0..n trade_order n──0..1 order_list
trade_order 1──n order_fill
trading_plan 1──0..1 trading_journal (đã có, uq_trading_journal_plan)
user_account 1──n equity_snapshot ──→ dashboard hiệu suất
```

Chuỗi `trade_order → trading_plan → trading_journal` nối lệnh với nghiệp vụ chính. Pha 1 chỉ có khóa; pha 2 (khi gộp engine) mới điền `plan_id` lúc plan được kích hoạt.

## 3. Thay đổi chi tiết

### 3.1 Migration `V34__paper_into_core_schema.sql` (một transaction)

Postgres chạy DDL trong transaction: một bước lỗi thì toàn bộ V34 rollback, DB giữ nguyên như trước.

1. **Kiểm tra tiền điều kiện** (`DO` block, `RAISE EXCEPTION` nếu sai):
   - `paper_position`, `paper_funding_payment`, `paper_futures_setting` rỗng.
   - Mỗi `paper_transfer` có đúng 2 dòng ledger `TRANSFER` cùng ref.
   - Ghi lại số dòng từng bảng vào bảng tạm để đối chiếu ở bước 8.
2. Thêm `user_id` vào 6 bảng, backfill qua `paper_account`, đặt `NOT NULL`, FK `user_account`, index (đúng quy ước V1: FK là cột đầu của một index).
3. Dựng lại các unique trên `user_id`:
   - `(user_id, wallet_type, coin_id)`
   - `(user_id, client_order_id)`
   - `(user_id, list_client_order_id)` (V30)
   - `(user_id, snapshot_date)`
4. Ledger:
   - Thêm `client_transfer_id varchar(64)`, backfill từ `paper_transfer` cho cả 2 dòng.
   - Unique một phần `(user_id, client_transfer_id) WHERE entry_type = 'TRANSFER' AND amount < 0`: giữ idempotency của transfer.
   - Đổi ref `ACCOUNT` → `USER` (ref_id = user_id) và sửa CHECK.
   - Unique một phần `(user_id, wallet_type, coin_id) WHERE entry_type = 'INITIAL_GRANT'`: thay `uq_paper_account_user`, chặn mở tài khoản 2 lần khi có request đồng thời.
5. `trade_order.plan_id uuid NULL` + FK `trading_plan` + index.
6. Xóa cột `account_id` và FK cũ; đổi tên bảng, constraint, index theo tên mới (để `expected-columns.csv` và các thông báo lỗi khớp quy ước).
7. Đổi tên `paper_account` → `legacy_paper_account`, `paper_transfer` → `legacy_paper_transfer` (bỏ FK ra ngoài). Xóa 3 bảng Futures rỗng.
8. **Kiểm tra hậu điều kiện:**
   - Số dòng từng bảng bằng bước 1.
   - Bất biến ledger: tổng các dòng = `free + locked` theo `(user_id, wallet_type, coin_id)`.
   - Không còn dòng nào có `user_id` NULL.
   - Sai một điều kiện → `RAISE` → rollback toàn bộ.

### 3.2 Backend (`paper` package; API giữ nguyên)

| Nhóm | Việc |
|---|---|
| Entity | Xóa `PaperAccount`, `PaperTransfer`. Đổi `@Table` của 6 entity; `accountId` → `userId`. Thêm `planId` vào `PaperOrder`. Thêm `clientTransferId` vào `PaperLedgerEntry`. |
| Repository | Sửa mọi native query (tên bảng, `account_id`). Viết lại `PaperTransferRepository` thành query ledger (dòng `TRANSFER` có `amount < 0`, ghép với dòng đối ứng). Xóa `PaperAccountRepository`. |
| Service | 14 file dùng `PaperAccount` chuyển sang `userId`. "Đã mở tài khoản" = đã có `INITIAL_GRANT`; `openedAt` lấy từ dòng đó. Bắt vi phạm unique INITIAL_GRANT → trả về tài khoản đã có, như cũ. |
| DTO | `PaperAccountResponse(Instant openedAt)`: bỏ `accountId` và `positionMode` (FE sửa theo, §3.3). `TransferResponse` giữ nguyên các field. |
| Enum | Xóa `PositionMode`; `LedgerRefType` đổi `ACCOUNT` → `USER`. |
| Kiến trúc | Thêm test ArchUnit: chỉ package `paper` được ghi các bảng ví/lệnh; `trading` không phụ thuộc vào `paper` (giữ ranh giới cho pha 2). |
| Tài liệu trong code | Sửa header V21 không được (Flyway checksum); ghi chú mô hình mới ở đầu V34. |

Các thứ **không đổi:** engine paper, `PriceLevelBook`, STOMP `/user/queue/*`, mã lỗi, giới hạn đặt lệnh, toàn bộ module `trading`.

### 3.3 Frontend (nhánh riêng, sau khi pull `develop`)

- `types/domain.ts`: `PaperAccount` bỏ `positionMode` (và `PaperPositionMode` nếu không còn chỗ dùng).
- `services/api/paper-dto.ts`: parser account chỉ đọc `openedAt`; parser cũ phải không vỡ nếu BE cũ còn trả field thừa (đọc lỏng, bỏ qua field lạ).
- `dev/dev-paper-trading.ts`: mock bỏ `positionMode`.
- `docs/api/api-contract.md`: sửa mục paper account. File này đang có thay đổi local chưa commit của bạn: mình chỉ commit phần của mình (`git add -p`), không đụng phần của bạn.
- Test: `paper-http.test.ts` và các test dùng mock account.

### 3.4 Tài liệu (`cryptopilot-docs`)

- ERD conceptual/logical mới.
- Decision D-117 (P1–P7), sửa mục TR-02 trong CURRENT_STATE, ghi chú pha 2 vào `paper-trading-plan.md`.
- SRS mặc định do leader sửa; mình chỉ chuẩn bị đoạn đề xuất.

## 4. Trình tự thực thi

| Bước | Việc | Điều kiện qua bước |
|---|---|---|
| 0 | `feat/admin-console` (`2d3c8e9`, V33) đã push nhưng chưa có PR/chưa merge → tạo nhánh PCI từ tip `2d3c8e9`; PR của PCI chỉ mở/merge sau khi PR admin-console đã merge, rồi rebase lên develop | V33 nằm trước V34 trên develop |
| 1 | `pg_dump` DB local hiện tại (có dữ liệu QA thật) → scratchpad | file dump khôi phục được |
| 2 | BE: nhánh `refactor/paper-into-core-schema` từ develop | — |
| 3 | Viết V35 + test migration (§6.1), chạy trên DB rỗng và trên bản dump | test xanh, số dòng khớp |
| 4 | Sửa entity / repository / service; cập nhật `expected-columns.csv`, `expected-enums.csv`, `PaperTradingSchemaTest`, `BaselineSchemaTest` | `mvnw verify` xanh toàn bộ (hiện ~3350 test) |
| 5 | FE: pull develop, nhánh `refactor/paper-account-shape` | `npm run lint`, `typecheck`, `test`, `build` xanh |
| 6 | System test (§6.3) với BE + FE chạy thật trên DB đã migrate từ dump | toàn bộ kịch bản đạt |
| 7 | Push 2 nhánh, mở 2 PR (BE trước, FE sau), mô tả rõ thứ tự merge và cách khôi phục | — |
| 8 | Tài liệu (§3.4) | — |

## 5. Rủi ro và cách sửa nhanh

### 5.1 Bảng rủi ro

| Tình huống xấu | Phòng ngừa | Nếu vẫn xảy ra |
|---|---|---|
| V34 lỗi giữa chừng trên máy thành viên | Một transaction + kiểm tra trước/sau | DB tự rollback, app không khởi động và báo rõ lý do; sửa V34 rồi chạy lại (chưa được ghi vào lịch sử Flyway) |
| V34 chạy xong nhưng dữ liệu sai logic | Đối chiếu số dòng và bất biến ledger trong migration | Dữ liệu gốc còn trong `legacy_paper_*` → viết V35 sửa tiến (Flyway không đi lùi) |
| Có thành viên đã chạy V34 rồi nhận V33 muộn (lỗi thứ tự Flyway) | Bước 0: V33 merge trước | Đánh số lại migration (V34 → V35); DB local của người đó chạy `flyway repair` hoặc dựng lại DB, có hướng dẫn trong PR |
| Thành viên đang có nhánh sửa paper → conflict | Kiểm tra: PT-F1/PT-F2 đã merge, chỉ admin-console (của mình) còn đụng | Rebase giúp; tên entity/class Java giữ nguyên nên conflict nhỏ |
| BE1 bị ảnh hưởng | Không sửa `trading/`, không đụng `matching_watermark` | Test ArchUnit chặn phụ thuộc chéo |
| FE cũ gặp BE mới (merge lệch nhau) | Parser FE đọc lỏng; BE chỉ bớt field | FE cũ vẫn chạy nếu chỉ thiếu `positionMode`; nếu không, merge FE ngay sau BE |
| Mở tài khoản đồng thời tạo grant 2 lần | Unique một phần trên INITIAL_GRANT | Test đồng thời (§6.1) |
| Transfer bị trùng khi retry | Unique một phần `client_transfer_id` | Test idempotency có sẵn phải xanh |
| Hiệu năng query đổi | Giữ đủ index như cũ, theo `user_id` | So sánh `EXPLAIN` các query nóng (open orders, fills, ledger) trước/sau |
| Cần quay lại hẳn (revert) | PR nhỏ gọn, tách commit | Trước khi chạy trên DB chung: revert PR. Sau đó: không revert migration, phải viết migration sửa tiến (dữ liệu legacy vẫn còn) |

### 5.2 Lưới an toàn dữ liệu

- `legacy_paper_account` và `legacy_paper_transfer` giữ nguyên dữ liệu gốc, không ai ghi vào.
- File dump bước 1.

### 5.3 Dọn dẹp

`V35__drop_legacy_paper_tables.sql` ở PR riêng, sau khi develop chạy ổn tối thiểu 1 tuần và cả nhóm xác nhận.

## 6. Kiểm thử

### 6.1 Migration (Testcontainers)

- Migrate tới V33 → nạp dữ liệu mẫu đủ loại: 2 user, grant, transfer 2 chiều, lệnh LIMIT/MARKET/STOP_LIMIT, OCO/OTOCO, fill, equity snapshot, watermark → migrate V34 → assert:
  - số dòng giữ nguyên;
  - bất biến ledger đúng;
  - `user_id` đúng chủ;
  - `client_transfer_id` có ở cả 2 dòng của mỗi transfer;
  - các unique mới hoạt động.
- Tiền điều kiện: có 1 dòng trong `paper_position` → V34 phải dừng và DB không đổi.
- Cùng bộ kiểm tra chạy trên bản dump DB local thật.

### 6.2 Tự động

- `mvnw verify` toàn bộ, chạy 2 lần (bắt flaky; đã biết `AlertEngineTest.NSF06` flaky sẵn).
- Bộ test paper (~291) phải xanh mà không sửa assert hành vi; chỉ sửa chỗ tạo dữ liệu theo schema mới.
- Thêm:
  - mở tài khoản đồng thời;
  - transfer idempotency sau khi chuyển sang ledger;
  - ArchUnit ranh giới `trading`/`paper`.
- FE: lint, typecheck, unit test, build.

### 6.3 System test (BE + FE chạy thật, Chrome, ghi GIF)

Trên DB migrate từ dump (tài khoản QA cũ) và trên một tài khoản mới:

1. Đăng nhập → mở tài khoản paper (tài khoản mới) / thấy số dư cũ đúng (tài khoản QA).
2. Chuyển SPOT ↔ FUTURES, gửi lại cùng `clientTransferId` → không trùng; lịch sử transfer hiển thị như trước.
3. Spot: MARKET mua/bán, LIMIT treo rồi khớp, LIMIT_MAKER, STOP_LIMIT, OCO, OTOCO, hủy 1 lệnh, hủy tất cả.
4. Bị từ chối vì filter (tick/step/minNotional) → thông báo đúng.
5. Open orders, order history, fill history, ledger, Spot PnL, equity hiển thị đúng; STOMP cập nhật realtime.
6. Restart BE khi có lệnh treo → replay khớp đúng (watermark).
7. **Hồi quy phần không đụng:** plan Spot/Futures: calculate, tạo, kích hoạt, hủy, khớp entry; alert; forum; admin (nếu admin-console đã merge).
8. So sánh kết quả số dư/PnL với ảnh chụp trước khi migrate.

## 7. Pha 2 (ngoài phạm vi, ghi lại để không mất)

- Plan kích hoạt → đặt `trade_order` (entry + OCO SL/TP) qua engine paper; một engine; gộp watermark.
- Engine paper hỗ trợ Futures (đòn bẩy, liquidation, funding từ `funding_rate_history`); vị thế ghi vào `trading_journal`.
- Làm cùng BE1, sau TP-B và T-048.

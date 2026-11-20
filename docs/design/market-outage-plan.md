*Plan · Module market + paper + trading + watchlist + notification · bản nháp để team đọc trước khi làm*

# CryptoPilot: tạm dừng giao dịch khi mất dữ liệu Binance, giá dự phòng chỉ để xem

- **Ngày:** 19/11/2026
- **Người viết:** BE3
- **Quyết định:** D-159 (trong code ghi D-158 tới tối 20/11, mã đó đã thuộc T-074b), PR #111
- **Căn cứ code:** BE `feat/community-member-page` @ `7a2a2400` (module `market`, `paper`, `trading`, `watchlist`, `notification` giống `develop`), FE `develop`.
- **Thay thế:** hướng "OKX dự phòng cho cả khớp lệnh Spot" bàn ngày 17/11. Hướng mới: **giá dự phòng chỉ để hiển thị, không bao giờ dùng để khớp lệnh, thanh lý hay tính funding.**

> **Cách đọc.** Mục 1–3 là nguyên tắc và hiện trạng. Mục 4–9 là thiết kế: trạng thái, hành vi từng chức năng, người đang giao dịch dở, quy trình khôi phục, thông báo. Mục 10–15 là API, dữ liệu, tình huống biên, kiểm thử, task, quyết định cần chốt.

---

## 1. Mục tiêu và nguyên tắc bất biến

**Mục tiêu.** Khi mất dữ liệu giá Binance:
1. Không có lệnh, thanh lý hay funding nào bị tính bằng giá sai.
2. Người dùng **biết ngay** là đang tạm dừng, vì sao, từ lúc nào, và tài sản của họ ra sao.
3. Khi có lại dữ liệu, hệ thống tự đồng bộ cho đúng như Binance đã diễn ra, rồi **báo rõ** đã mở lại và chuyện gì đã xảy ra với lệnh của họ.

**Bất biến (mọi thiết kế và test bên dưới phải giữ):**

| # | Bất biến |
|---|---|
| I1 | Mọi lần khớp, kích hoạt, thanh lý, funding và hết hạn theo thời gian chỉ dựa trên dữ liệu **Binance**. Giá dự phòng không bao giờ đi vào `MarketApi` mà `paper`, `trading`, `watchlist` dùng. |
| I2 | Khi một thị trường (Spot hoặc Futures) đang `PAUSED` hoặc `RECOVERING`, không thao tác nào của người dùng làm thay đổi lệnh, vị thế hay số dư trên thị trường đó được chấp nhận (trừ các ngoại lệ ghi rõ ở mục 5). |
| I3 | Không có gì bị mất: lệnh, vị thế và lệnh điều kiện đang chờ lúc bắt đầu tạm dừng vẫn còn nguyên khi mở lại, và được xử lý như Binance đã chạy trong khoảng mất dữ liệu. |
| I4 | Không có gì bị làm hai lần: một nến được replay hai lần cũng không khớp hai lần, một kỳ funding không bị tính hai lần (đã có sẵn: replay idempotent, funding idempotent theo position và kỳ). |
| I5 | Thứ tự đúng như thời gian thật: một vị thế mà replay cho thấy đã bị thanh lý trước giờ funding thì không bị tính funding kỳ đó. Một lệnh GTD hay một plan mà replay cho thấy đã khớp trước giờ hết hạn thì là khớp, không phải hết hạn. |
| I6 | Giao dịch chỉ mở lại khi mọi cặp có lệnh hoặc vị thế đã replay xong tới hiện tại. |
| I7 | Người dùng luôn thấy trạng thái hiện tại: banner toàn trang, form đặt lệnh bị khóa kèm lý do, và nhãn nguồn trên mọi con số giá dự phòng. |

---

## 2. Hiện trạng code dùng lại được

Phần lớn "xử lý người đang trade dở" **đã có sẵn** vì hệ thống đã phải chịu được việc mất stream vài giây và khởi động lại:

| Có sẵn | Ở đâu | Dùng cho kế hoạch này |
|---|---|---|
| Watermark và replay nến 1 phút đã đóng cho các cặp có lệnh chờ (Spot và Futures paper) | `paper/job/PaperMatchingWorker` (Q-T6, D-77, D-78), `replay.max-window` mặc định **24h** | Khớp bù toàn bộ khoảng mất dữ liệu bằng nến Binance thật |
| Replay cho plan và vị thế journal | `trading/job/MinuteKlineFeed`, `MatchingWorker`, `max-window` mặc định **7d** | Như trên cho module `trading` |
| `MARK_STALE`: mark quá `mark-max-age` (5s) thì cặp Futures bị khóa mở rủi ro, chỉ cho đóng và hủy; replay mark candles rồi mới live lại | `FuturesMargins`, `FuturesMarkCatchUp`, `FuturesTrigger` (TR-22a, TR-42) | Đã khóa từng cặp. Kế hoạch thêm khóa toàn thị trường và khóa luôn đóng/hủy (mục 5) |
| Backfill nến khi stream nối lại | `market/job/CandleBackfillJob` (`MarketStreamReconnected`, `GapDetected`, NSF-02/03) | Bước đầu tiên của khôi phục |
| Nhớ IP ban 418 qua restart | `BinanceBanStore`, `PersistentBinanceBans` | Một nguyên nhân tạm dừng; biết trước `retryAt` |
| Funding tính từ các kỳ đã lưu, idempotent, `lookback` 2d | `paper/job/FuturesFundingJob`, `FuturesFunding` | Funding bù sau khi Binance trả lịch sử `/fapi/v1/fundingRate` |
| Tiếp tục cross liquidation dở dang | `FuturesLiquidationSafetyJob` | Thanh lý đang chạy lúc mất dữ liệu |
| Lỗi `MARKET_PRICE_UNAVAILABLE` (503, MSG43) | `ErrorCode` | Hiện bị "mượn" nhiều chỗ. Kế hoạch đề xuất mã riêng (mục 10.3) |
| Alert không tính cắt qua từ giá cũ hơn `staleness` 5m | `watchlist/job/AlertEngine` | Alert không bắn hồi tố sau sự cố |
| Thông báo in-app, chuông, `NotificationType.SYSTEM` (cho admin) | module `notification`, FE `features/notifications` | Thông báo cá nhân lúc dừng và lúc mở lại |
| STOMP `/topic/ticker|kline|depth|trades|overview…` | `MarketBroadcastService`, FE `stomp-market-feed.ts` | Thêm `/topic/market.status` |

**Còn thiếu:** trạng thái sức khỏe cấp thị trường, cổng chặn chung, nguồn giá dự phòng chỉ để xem, thứ tự khôi phục cho các job theo thời gian (funding, GTD, plan expiry), bản ghi sự cố, toàn bộ thông báo và giao diện.

---

## 3. Phân loại sự cố

| Loại | Ví dụ | Binance có giao dịch trong lúc đó không? | Sau khi có lại |
|---|---|---|---|
| **A. Binance dừng thật** | Bảo trì, sự cố sàn | **Không**, hoặc chỉ một phần | Nến của khoảng đó trống hoặc thiếu → replay không khớp gì, chạy tiếp từ giá mới |
| **B. Mình mất kết nối, Binance vẫn chạy** | Mạng EC2, DNS, WebSocket rớt mãi không nối lại, IP bị 429/418 | **Có** | Replay nến Binance thật → kết quả **đúng như Binance** |
| **C. Mất một phần** | Chỉ Futures (`fstream`) rớt, Spot vẫn chạy; một shard stream rớt | Có | Chỉ thị trường hoặc cặp bị ảnh hưởng tạm dừng |
| **D. Server mình khởi động lại hoặc deploy** | Restart BE | Có | Đã có replay lúc start. Chỉ cần mở trạng thái đúng sau restart (mục 12) |
| **E. Cả nguồn dự phòng cũng hỏng** | OKX cũng lỗi | — | Màn hình hiện "không có dữ liệu giá", phần còn lại như A/B |
| **F. REST bị cấm nhưng WS vẫn chạy (hoặc ngược lại)** | 418 trên REST | Có | Live chạy được nhưng **replay không chạy được** → cặp nào cần replay vẫn chờ |

Hệ thống **không cần biết** đang là A hay B: cứ replay theo nến Binance trả về. A thì không khớp gì, B thì khớp đúng. Chỉ cần kiểm chứng replay không bị kẹt khi Binance trả thiếu nến ở loại A (task K3, mục 14).

---

## 4. Máy trạng thái sức khỏe dữ liệu (theo từng thị trường)

Mỗi thị trường `SPOT`, `FUTURES` có một trạng thái riêng, vì hai stream khác host (`stream.binance.com` và `fstream.binance.com`).

```
           dữ liệu chậm > 10s                im > 30s, hoặc REST và WS cùng lỗi, hoặc admin bật bảo trì
  LIVE ───────────────────────▶ RECONNECTING ─────────────────────────────▶ PAUSED
   ▲   ◀─────────────────────────┘ có lại trong 30s                            │
   │        (không thông báo gì)                                               │ WS live lại ≥ 15s liên tục
   │                                                                           │ và REST trả lời được
   │                                                                           ▼
   └──────────────── mọi cặp có lệnh/vị thế/plan đã replay xong ──────── RECOVERING
                     + funding, GTD, plan expiry đã chạy bù                   │
                     (mở giao dịch, thông báo "đã hoạt động lại")              │ rớt lại
                                                                              ▼
                                                                            PAUSED (cùng sự cố, không mở bản ghi mới)
```

| Trạng thái | Ý nghĩa | Giao dịch | Hiển thị |
|---|---|---|---|
| `LIVE` | Bình thường | Mở | Bình thường |
| `RECONNECTING` | Rớt ngắn, đang tự nối lại (ReconnectBackoff, thử host Binance khác) | Như hiện nay: các luật stale có sẵn theo cặp (MSG43, `MARK_STALE`) | Chấm vàng nhỏ "Đang kết nối lại…", **không** banner, **không** thông báo |
| `PAUSED` | Mất dữ liệu thật | **Đóng** (mục 5) | Banner đỏ, giá từ nguồn dự phòng kèm nhãn |
| `RECOVERING` | Binance có lại, đang backfill và replay | **Vẫn đóng** | Banner xanh dương "Đang đồng bộ lại…" và tiến độ |
| `MAINTENANCE` (biến thể của `PAUSED`) | Admin bật tay (biết trước lịch bảo trì Binance, hoặc tự deploy) | Đóng | Banner với lời nhắn của admin |

**Ngưỡng** để trong `application.yml` (`cryptopilot.market.health.*`): `reconnecting-after` 10s, `pause-after` 30s, `stable-before-recover` 15s, `poll-interval` 1s. Thời điểm bắt đầu sự cố là **thời điểm có dữ liệu live cuối cùng**, không phải lúc phát hiện.

**Trường hợp chỉ vài cặp mất dữ liệu** (một shard rớt): thị trường vẫn `LIVE`, các cặp đó dùng luật stale theo cặp có sẵn, và có thêm cờ `pairPaused` trong `/market/status` để FE khóa form của riêng cặp đó. Nếu quá `pause-ratio` (mặc định 50%) số cặp đang theo dõi bị mất, cả thị trường chuyển `PAUSED`.

**Chống nhảy qua nhảy lại:** `RECOVERING` rớt lại thì quay về `PAUSED` **cùng bản ghi sự cố** (không gửi thêm thông báo "đã tạm dừng"). Mỗi người dùng chỉ nhận tối đa 1 thông báo "tạm dừng" và 1 thông báo "đã mở lại" cho mỗi sự cố.

Thành phần: `market/service/MarketHealthService` (đọc), `market/job/MarketHealthMonitor` (job 1s, đọc thời điểm tin nhắn cuối của mỗi shard từ `MarketStreamSupervisor` và kết quả gọi REST gần nhất từ `BinanceRequestGate`), phát sự kiện `MarketTradingPaused`, `MarketRecoveryStarted`, `MarketTradingResumed`. Đặt các sự kiện này trong `market/event` để module khác lắng nghe mà không phụ thuộc vào bên trong `market`.

---

## 5. Hành vi từng chức năng theo trạng thái

✅ cho phép · ⛔ chặn với mã `TRADING_PAUSED` · ⏸ đóng băng, chạy bù khi `RECOVERING` · 👁 dùng giá dự phòng có nhãn

| Chức năng | LIVE | PAUSED | RECOVERING | Ghi chú |
|---|---|---|---|---|
| Đặt lệnh Spot/Futures (mọi loại: MARKET, LIMIT, STOP…, TRAILING) | ✅ | ⛔ | ⛔ | Kể cả LIMIT không cần giá hiện tại: tránh đặt lệnh dựa vào giá dự phòng |
| Lệnh điều kiện Futures (`algoOrder`), TP/SL gắn vị thế | ✅ | ⛔ | ⛔ | |
| **Hủy, sửa (amend) lệnh** | ✅ | ⛔ *(Q1)* | ⛔ | Xem lý do ở mục 6.3 |
| Đóng vị thế Futures (market/limit/close-all) | ✅ | ⛔ | ⛔ | Cần mark và last price |
| Đổi đòn bẩy, margin type, position mode, thêm/bớt ký quỹ | ✅ | ⛔ | ⛔ | Cần mark để kiểm tra ký quỹ |
| Chuyển tiền vào ví Futures | ✅ | ✅ | ✅ | Không cần giá, chỉ làm tăng ký quỹ |
| Chuyển tiền ra khỏi ví Futures | ✅ | ⛔ | ⛔ | Số rút được phụ thuộc PnL chưa chốt |
| Tạo, kích hoạt, đóng plan (`trading`) | ✅ | ⛔ (bản nháp ✅) | ⛔ (bản nháp ✅) | |
| Hủy plan đang chờ | ✅ | ⛔ *(Q1)* | ⛔ | Cùng lý do với hủy lệnh |
| Khớp lệnh chờ, kích hoạt trigger, trailing | live | ⏸ | replay | Engine không nhận dữ liệu live, replay khi có lại |
| Thanh lý isolated/cross, margin call | live | ⏸ | replay rồi live | Thanh lý dở dang được `FuturesLiquidationSafetyJob` tiếp tục |
| Funding (`FuturesFundingJob`) | ✅ | ⏸ | ⏸ tới khi replay mark của cặp qua giờ funding | Giữ I5 (mục 7, bước 4) |
| Hết hạn GTD (`FuturesGoodTillJob`), hết hạn plan (`PlanExpiryJob`) | ✅ | ⏸ | ⏸ tới khi watermark của cặp ≥ giờ hết hạn | Giữ I5 |
| Hủy lệnh do cặp ngừng giao dịch (`PairStopListener`, `PaperPairStopSweep`) | ✅ | ✅ | ✅ | Do admin hoặc Binance quyết, không phụ thuộc giá |
| Ảnh chụp equity (`PaperEquitySnapshotJob`), grant cost | ✅ | ⏸ (đã có retry PT-R02) | ⏸ | Không dùng giá dự phòng |
| Alert giá, funding, OI, indicator | ✅ | ⏸ | ⏸ | Không bắn hồi tố (`staleness` 5m). Tạo/sửa alert vẫn ✅ |
| Tạo, sửa alert | ✅ | ✅ | ✅ | Không cần giá |
| Ticker, overview, `/markets`, sparkline | Binance | 👁 | 👁 rồi Binance | |
| Biểu đồ nến | Binance | Nến Binance đã lưu + nến dự phòng (không lưu DB, vẽ khác màu) 👁 | Backfill xong thì FE tải lại | |
| Order book, recent trades | Binance | Ẩn, hiện "Tạm ngưng" | Ẩn tới khi `LIVE` | Order book dự phòng dễ gây hiểu nhầm |
| Indicator, setup score, phân tích AI | Binance | Hiện số cuối kèm "Dữ liệu tới hh:mm" | Như PAUSED | Không tính từ nến dự phòng |
| Số dư, lịch sử lệnh, PnL đã chốt | ✅ | ✅ | ✅ | |
| PnL chưa chốt, giá thanh lý ước tính | Binance | Hiện theo **mark Binance cuối**, ghi rõ "tạm tính tới hh:mm", **không** dùng giá dự phòng | Như PAUSED | Tránh làm người dùng hoảng vì một con số không dùng thật |
| Community, news, academy, billing, profile | ✅ | ✅ | ✅ | Không liên quan |

**Cổng chặn duy nhất:** `MarketHealthService.requireTrading(MarketType)` gọi ở đầu mọi service thay đổi trạng thái giao dịch (`PaperOrderServiceImpl`, `FuturesOrderServiceImpl`, `FuturesAlgoServiceImpl`, `FuturesPositionServiceImpl`, `FuturesAccountServiceImpl`, `FuturesConfigService…`, `TradingPlanServiceImpl`, `PositionServiceImpl`, `PositionLevelServiceImpl`). Kiểm tra **bên trong** khóa paper của Trader, cùng transaction, để một request đang chạy đúng lúc chuyển trạng thái chỉ có hai kết cục: xong trọn vẹn trước, hoặc bị từ chối. Thêm ArchUnit test: mọi method public có `@Transactional` ghi trong các service trên phải đi qua cổng (hoặc liệt kê ngoại lệ có chủ đích).

---

## 6. Người đang giao dịch dở lúc bị dừng

### 6.1 Từng loại "đang dở" và cách xử lý

| Đang dở | Trong lúc PAUSED | Khi RECOVERING / mở lại | Người dùng thấy gì |
|---|---|---|---|
| Request đặt lệnh **đang bay** đúng lúc chuyển trạng thái | Cổng kiểm tra trong khóa: hoặc đã commit trước (lệnh hợp lệ, sẽ được replay), hoặc bị 503 `TRADING_PAUSED` | — | Toast "Giao dịch đang tạm dừng, lệnh chưa được gửi" |
| MARKET Spot đã gửi, đã khớp trước khi dừng | Không ảnh hưởng | — | Bình thường |
| LIMIT / STOP_LIMIT / TAKE_PROFIT Spot đang chờ | Giữ nguyên `NEW`, không khớp | Replay nến Binance từ watermark: khớp nếu giá đã chạm, **thời gian khớp = thời gian nến** (D-78) | Thông báo tổng kết liệt kê lệnh khớp trong lúc dừng |
| Trailing stop đang theo giá | Đóng băng đỉnh/đáy đã lưu | Replay cập nhật đỉnh/đáy theo nến rồi kích hoạt nếu cần | Như trên |
| Lệnh vừa đặt **chưa được engine theo dõi** (untracked) | Đã có cơ chế giữ recent trades | Replay theo thời điểm đặt (D-77: nến trước lúc đặt không khớp nó) | — |
| LIMIT Futures chờ, lệnh điều kiện theo last/mark | Giữ nguyên | Replay last candles rồi mark candles của cùng phút (TECHNICAL_DESIGN 7.7) | Như trên |
| Vị thế Futures isolated đang mở | Không thanh lý, không margin call | Mark catch-up: nếu mark đã chạm giá thanh lý → thanh lý. Có sẵn: thanh lý ghi theo **thời điểm áp dụng**, không ghi lùi | Thông báo FUTURES có sẵn (TR-43) + dòng trong tổng kết |
| Vị thế cross | Như trên, `crossState` conservative coi cặp đang dừng là rủi ro | Như trên, bước của cross liquidation đi theo thứ tự | Như trên |
| Cross liquidation **đang chạy dở** lúc dừng | `ForceClose` của cặp đã dừng nằm chờ | `FuturesLiquidationSafetyJob` tiếp tục sau khi mở lại | Như trên |
| Kỳ funding rơi vào khoảng dừng | Không tính | Đợi Binance trả `fundingRate` của kỳ đó và mark replay đã qua giờ funding, rồi tính đúng rate thật | Dòng "Funding 16:00 đã được tính: −0.42 USDT" |
| Lệnh GTD hết hạn trong khoảng dừng | Không hết hạn | Chỉ hết hạn sau khi watermark của cặp qua `goodTillDate`. Nếu replay khớp trước thì là khớp | Đúng như Binance |
| Plan (`trading`) chờ entry, vị thế journal có SL/TP | Giữ nguyên | `MinuteKlineFeed` replay (cửa sổ 7d) | Thông báo PLAN có sẵn |
| Plan hết hạn trong khoảng dừng | Không hết hạn | Như GTD | |
| Alert đang bật | Không đánh giá | Chạy tiếp từ giá live, không hồi tố | Banner có dòng "Cảnh báo giá tạm ngưng" |
| Đang mở form đặt lệnh | Nút đặt lệnh khóa, ô nhập vẫn giữ nội dung | Mở khóa khi `LIVE` | Lý do ngay dưới nút |
| Đang ở trang Futures nhìn PnL | PnL đứng ở mark Binance cuối, nhãn "tạm tính" | Cập nhật lại | |

### 6.2 Sự cố dài hơn cửa sổ replay

`paper.replay.max-window` là 24h, `trading` 7d, funding `lookback` 2d. Sự cố dài hơn sẽ làm **mất** phút không replay (mã hiện tại bỏ qua kèm cảnh báo). Cách xử lý:

- Lưu sự cố vào DB (mục 11). Khi khôi phục, cửa sổ replay của paper và lookback của funding **được nới tới đầu sự cố**, tối đa 7 ngày (`max-outage-replay`).
- Quá 7 ngày (gần như không xảy ra): giữ trạng thái `RECOVERING` và báo admin (`SYSTEM`) để quyết định bằng tay. Không tự đoán giá.

### 6.3 Vì sao chặn cả hủy lệnh (Q1)

Trong lúc dừng, người dùng **nhìn thấy giá dự phòng** còn hệ thống chưa biết Binance đã chạy tới đâu. Nếu cho hủy, ai thấy giá sắp chạm lệnh thua lỗ sẽ hủy ngay. Sau đó replay cho thấy lệnh đó *đáng lẽ đã khớp* trước lúc hủy. Đây là một "quyền chọn miễn phí" để gian lận. Hai cách:

- **A. Chặn hủy (đề xuất).** Đơn giản, công bằng. Sàn thật lúc dừng cũng không cho hủy. Banner giải thích lý do.
- **B. Nhận yêu cầu hủy, áp dụng sau replay.** Lưu yêu cầu kèm thời điểm T. Replay tới T: nếu lệnh đã khớp trước T thì báo "đã khớp trước khi hủy", nếu chưa thì hủy tại T. Đúng nhất nhưng tốn thêm khoảng 2–3 ngày làm và kiểm thử.

---

## 7. Quy trình khôi phục (`RECOVERING`), theo đúng thứ tự

Chạy cho từng thị trường, tự động, không cần người bấm:

1. **Xác nhận ổn định.** WS live liên tục ≥ `stable-before-recover` và một lần gọi REST thành công (không bị 429/418/circuit open).
2. **Backfill nến.** `CandleBackfillJob` (đã được `MarketStreamReconnected` kích hoạt) lấp nến từ đầu sự cố, cho cả mark price klines của Futures. FE nhận `market.status` có tiến độ.
3. **Replay engine.** `PaperMatchingWorker` và `MinuteKlineFeed` replay từ watermark (đã có). Với cặp Futures: last candles rồi mark candles cùng phút, sau đó mark catch-up kết thúc như hiện nay.
4. **Job theo thời gian chạy bù có điều kiện:**
   - Funding: kỳ `t` của một cặp chỉ được tính khi mark catch-up của cặp đó đã qua `t` **và** `fundingRate` kỳ `t` đã có trong DB. Chỉ chặn thứ tự là **chưa đủ**: thanh lý trong replay ghi `closedAt = lúc áp dụng` (TR-42), nên điều kiện "đang mở lúc `t`" của `FuturesFunding` vẫn tính funding cho vị thế mà mark đã chạm giá thanh lý trước `t`. Sửa: lệnh đóng của thanh lý replay ghi `source_time` = thời điểm của mark đã chạm (như fill replay đã làm với nến), và funding coi vị thế đóng từ `min(closed_at, source_time của lệnh đóng)`. Không thêm cột.
   - GTD và plan expiry: chỉ hết hạn lệnh của cặp có watermark ≥ thời điểm hết hạn.
   - Equity snapshot, grant cost: retry có sẵn.
5. **Kiểm tra cổng mở:** mọi cặp có lệnh, vị thế hoặc plan đều có watermark ≥ phút hiện tại − 1, không còn cặp nào `MARK_STALE` do sự cố, funding đã tính bù hết.
6. **Mở giao dịch** → `LIVE`, đóng bản ghi sự cố, phát `MarketTradingResumed`.
7. **Gửi tổng kết** cho từng người dùng bị ảnh hưởng (mục 8.3).

Thời gian dự kiến: sự cố 1 giờ khoảng 1–3 phút đồng bộ (mỗi cặp vài request kline, trọng số Binance thấp). Có thời hạn `recovery-timeout` 15 phút: quá hạn thì báo admin nhưng **không** tự mở giao dịch.

---

## 8. Thông báo cho người dùng

### 8.1 Kênh

| Kênh | Khi nào | Ai thấy |
|---|---|---|
| **Banner toàn trang** (trên header, mọi trang đã đăng nhập và trang public `/markets`) | Ngay khi vào `PAUSED`, `RECOVERING`, `MAINTENANCE`; biến mất 60 giây sau khi `LIVE` (đổi sang màu xanh lá "đã hoạt động lại") | Tất cả |
| **Khóa form đặt lệnh** + dòng lý do dưới nút | `PAUSED`, `RECOVERING` | Người đang ở trang giao dịch |
| **Toast** | Khi trạng thái đổi trong lúc đang ở trang giao dịch; khi request bị 503 `TRADING_PAUSED` | Người đang ở trang |
| **Thông báo in-app (chuông)** | "Tạm dừng" chỉ gửi nếu sự cố kéo dài ≥ `notify-after` (2 phút), "đã mở lại + tổng kết" khi `LIVE` | Chỉ người **bị ảnh hưởng**: có lệnh chờ, vị thế, plan đang chạy hoặc alert bật trên thị trường đó |
| **Thông báo admin** (`NotificationType.SYSTEM`) | Vào `PAUSED`, quá `recovery-timeout`, sự cố > 7 ngày, nguồn dự phòng cũng hỏng | Admin |
| Email | **Không** gửi cho sự cố thường. Thanh lý vẫn theo kênh có sẵn của TR-43 | — |

FE nhận trạng thái qua STOMP `/topic/market.status`. Nếu WebSocket của chính server mình rớt, FE gọi lại `GET /api/v1/market/status` mỗi 15 giây, và luôn gọi một lần khi tải trang hoặc khi kết nối lại.

### 8.2 Nội dung (bản nháp, chốt với leader; giờ theo múi giờ người dùng)

**Banner `PAUSED`:**
> ⚠ **Tạm dừng giao dịch Futures** từ 14:32 do mất kết nối dữ liệu giá Binance. Lệnh, vị thế và số dư của bạn được giữ nguyên. Trong lúc này hệ thống không khớp lệnh, không thanh lý và không tính funding. Khi có lại dữ liệu, mọi thứ sẽ được xử lý đúng theo diễn biến thực tế của Binance. Giá đang hiển thị lấy từ **OKX, chỉ để tham khảo**.

**Banner `RECOVERING`:**
> 🔄 **Đã kết nối lại Binance.** Đang đồng bộ dữ liệu từ 14:32 đến 14:47 (đã xong 12/18 cặp). Giao dịch sẽ mở lại ngay khi đồng bộ xong.

**Banner `LIVE` sau sự cố (60 giây):**
> ✅ **Giao dịch Futures đã hoạt động lại** lúc 14:49 (tạm dừng 17 phút). Xem lệnh và vị thế được xử lý trong thời gian đồng bộ ở phần Thông báo.

**Banner `MAINTENANCE`:** lời nhắn admin nhập, kèm giờ dự kiến mở lại nếu có.

**Lý do dưới nút đặt lệnh:**
> Giao dịch đang tạm dừng vì mất dữ liệu giá Binance. Không thể đặt, hủy hoặc sửa lệnh lúc này.

**Lỗi API (`TRADING_PAUSED`):**
> Giao dịch trên thị trường {market} đang tạm dừng từ {since} do mất dữ liệu giá. Vui lòng thử lại sau khi hệ thống hoạt động trở lại.

**Nhãn giá dự phòng:** chip nhỏ cạnh giá `Nguồn: OKX · tham khảo`, giá màu xám nhạt.

### 8.3 Thông báo tổng kết cho từng người (khi `LIVE`)

Một thông báo in-app cho mỗi người bị ảnh hưởng, mỗi thị trường, mỗi sự cố:

> **Giao dịch Futures đã mở lại (tạm dừng 14:32–14:49).** Trong thời gian đó, theo diễn biến giá Binance:
> - 2 lệnh đã khớp: BTCUSDT LIMIT mua 0.01 @ 64,200 (14:36), ETHUSDT TP @ 3,410 (14:41)
> - 1 vị thế bị thanh lý: SOLUSDT long 10x
> - Funding 16:00 đã tính: −0.42 USDT
> - Không có thay đổi gì khác với lệnh đang chờ của bạn.

Bấm vào thông báo thì mở trang lịch sử lệnh, đã lọc theo khoảng thời gian sự cố. Không có gì xảy ra thì chỉ ghi "Lệnh và vị thế của bạn không bị ảnh hưởng."

Dữ liệu cho tổng kết: các fill, thanh lý và funding có `created_at` trong khoảng `RECOVERING` của sự cố, hoặc đánh dấu `fill_source = REPLAY` (đã có `FillSource`, cần kiểm tra giá trị).

---

## 9. Nguồn giá dự phòng (chỉ để xem)

- **Nguồn:** OKX public API (không cần key): spot tickers, swap tickers `*-USDT-SWAP`, candles, WebSocket `tickers`. Phải thử từ region EC2 trước khi chốt (Q2). Dự phòng thứ hai: Bybit.
- **Gói mới** `market/client/fallback` (`FallbackPriceClient`, `OkxClient`) + `market/service/DisplayPriceService`. Chỉ `MarketBroadcastService`, `CoinMarketServiceImpl` và controller hiển thị được dùng.
- **Cách ly (I1):** ArchUnit: `paper..`, `trading..`, `watchlist..` và `MarketApiImpl` không được phụ thuộc `market.client.fallback..` hay `DisplayPriceService`. Dữ liệu dự phòng **không ghi** vào `ohlcv`, `market_snapshot`, `futures_market_data`, cache giá dùng cho `MarketApi`.
- **Ánh xạ cặp:** `BTCUSDT` ↔ `BTC-USDT` (spot) / `BTC-USDT-SWAP` (futures), sinh tự động và cho admin sửa. Cặp không có trên OKX thì hiện "không có giá tham khảo".
- **Chỉ bật khi `PAUSED`/`RECOVERING`**: không tốn request lúc bình thường. Bật trong vòng ≤ 5 giây sau khi `PAUSED`.
- **Sai lệch quá lớn:** nếu giá OKX lệch > 5% so với giá Binance cuối thì vẫn hiện, nhưng thêm cảnh báo "Giá tham khảo có thể khác Binance đáng kể".
- **Payload hiển thị** có thêm `source: "BINANCE" | "OKX"` và `asOf`. FE vẽ nhãn từ `source`, không đoán.

---

## 10. API và realtime

### 10.1 REST

`GET /api/v1/market/status` (public, cache 1 giây):

```json
{
  "markets": [
    {
      "market": "FUTURES",
      "state": "RECOVERING",
      "tradingOpen": false,
      "since": "2026-11-19T07:32:05Z",
      "lastLiveAt": "2026-11-19T07:32:05Z",
      "reason": "STREAM_LOST",
      "displaySource": "OKX",
      "recovery": { "pairsDone": 12, "pairsTotal": 18, "replayedUntil": "2026-11-19T07:44:00Z" },
      "message": null,
      "incidentId": "…"
    },
    { "market": "SPOT", "state": "LIVE", "tradingOpen": true, "pausedPairs": [] }
  ]
}
```

`reason`: `STREAM_LOST`, `REST_UNAVAILABLE`, `RATE_LIMITED`, `IP_BANNED` (kèm `retryAt`), `MAINTENANCE`.

Admin: `POST /api/v1/admin/market/maintenance` `{ market, on, message, expectedEndAt }` (ghi audit log UC-46), `GET /api/v1/admin/market/incidents`.

### 10.2 STOMP

`/topic/market.status`: gửi cả payload trên mỗi khi trạng thái đổi, và mỗi 5 giây trong lúc `RECOVERING` (tiến độ).

### 10.3 Mã lỗi

`TRADING_PAUSED` (HTTP 503, **MSG mới**, đề xuất MSG57, leader chốt số và thêm vào SRS). Body có thêm `market`, `since`, `state`. Lý do không dùng lại MSG43: MSG43 là "không có giá của cặp này", FE cần phân biệt để hiện banner thay vì lỗi của một cặp.

---

## 11. Dữ liệu (migration mới)

Bảng `market_incident` (một migration, số V do người merge chốt):

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | uuid PK | |
| `market` | varchar(10) | `SPOT`/`FUTURES` |
| `kind` | varchar(20) | `OUTAGE`/`MAINTENANCE` |
| `reason` | varchar(30) | như `reason` ở 10.1 |
| `last_live_at` | timestamptz | đầu sự cố, dùng cho cửa sổ replay |
| `paused_at`, `recovery_started_at`, `resumed_at` | timestamptz | `resumed_at` null = đang mở |
| `message` | text null | lời nhắn admin |
| `created_by` | uuid null | admin nếu bật tay |

Ràng buộc: tối đa một bản ghi đang mở cho mỗi market (partial unique index `WHERE resumed_at IS NULL`). Dùng để: sống qua restart, nới cửa sổ replay, trang lịch sử sự cố cho admin, lọc tổng kết.

---

## 12. Tình huống biên phải xử lý

| # | Tình huống | Xử lý |
|---|---|---|
| E1 | Server restart trong lúc `PAUSED`/`RECOVERING` | Start đọc bản ghi đang mở → bắt đầu ở `PAUSED`, không bao giờ `LIVE` ngay. Replay lúc start đã có |
| E2 | Server restart lúc bình thường | Đang có replay lúc start. Thêm: giao dịch chỉ mở sau khi replay lúc start xong (hiện có thể đã mở sớm, cần kiểm tra) |
| E2b | Server restart khi có vị thế isolated mà không có lệnh điều kiện | **Phát hiện khi làm K7:** lúc khởi động, cặp chỉ có mức thanh lý chỉ replay mark của **phút hiện tại** (`PaperMatchingWorker.startupMarkReplay` lấy mốc muộn hơn giữa watermark và "bây giờ"). Mark của khoảng server tắt không được replay, nên thanh lý lẽ ra phải xảy ra sẽ bị bỏ qua. Sửa ở K3: replay từ mark watermark, tối đa tới đầu sự cố |
| E3 | Rớt rồi có lại liên tục (flapping) | Ngưỡng ổn định 15s, cùng bản ghi sự cố, mỗi người 1 thông báo |
| E4 | Chỉ Spot hoặc chỉ Futures mất | Trạng thái riêng từng thị trường. Ví Spot và Futures tách nên chuyển tiền giữa ví theo luật mục 5 |
| E5 | Vài cặp mất (một shard) | Luật theo cặp, `pausedPairs`, khóa form của cặp đó |
| E6 | WS lại nhưng REST bị 418 (`retryAt` xa) | Ở `PAUSED` với `reason = IP_BANNED`, banner hiện giờ dự kiến. Không mở khi chưa replay được |
| E7 | Binance trả thiếu nến (loại A) | Replay coi phút không có nến (khi Binance đã trả nến sau đó) là phút không giao dịch, không chờ mãi. **Cần kiểm chứng** trong `MinuteKlineFeed` và `PaperMatchingWorker` (K3) |
| E8 | Sự cố dài hơn cửa sổ replay | Mục 6.2 |
| E9 | Nguồn dự phòng cũng hỏng | Hiện "Không có dữ liệu giá", phần giao dịch không đổi. Báo admin |
| E10 | WebSocket của server mình tới FE rớt | FE poll `/market/status` 15s. Mọi request giao dịch vẫn được BE chặn nên không sai dữ liệu |
| E11 | Request đặt lệnh đang bay lúc chuyển trạng thái | Cổng kiểm tra trong khóa Trader và transaction (mục 5) |
| E12 | Người dùng mở nhiều tab | Mọi tab cùng nghe topic. Thông báo in-app idempotent theo (user, incident, loại) |
| E13 | Admin bật bảo trì lúc đang có sự cố | Gộp vào bản ghi đang mở, đổi `kind`. Tắt bảo trì thì đi qua `RECOVERING` như thường |
| E14 | Admin tắt bảo trì nhưng Binance vẫn mất | Vẫn `PAUSED` (`STREAM_LOST`). Admin không thể mở giao dịch khi không có dữ liệu |
| E15 | Kỳ funding ngay lúc mở lại | Bước 4 của mục 7 |
| E16 | Thanh lý cross đang chạy dở trên cặp khác | `FuturesLiquidationSafetyJob` + cặp kia replay xong mới đóng được |
| E17 | Đồng hồ server lệch | Dùng `eventTime` của Binance cho `lastLiveAt`. Ngưỡng tính bằng `Clock` của server; cảnh báo nếu lệch > 5s |
| E18 | Demo hoặc thuyết trình | Admin bật `MAINTENANCE` để demo toàn bộ luồng mà không cần làm sập mạng |

---

## 13. Kiểm thử (viết ma trận trước, sửa code sau)

**M1. Ma trận cổng chặn** (parameterized, `@SpringBootTest` + MockMvc): {LIVE, RECONNECTING, PAUSED, RECOVERING, MAINTENANCE} × {Spot, Futures} × mọi endpoint ghi ở mục 5 (đặt từng loại lệnh, hủy, amend, đóng, leverage, margin, chuyển tiền vào/ra, plan, alert) → mong đợi ✅ hoặc 503 `TRADING_PAUSED` đúng như bảng. Thị trường kia luôn ✅.

**M2. Ma trận replay** (giá trong khoảng dừng): {LIMIT mua/bán, STOP_LIMIT, TP/SL, TRAILING, Futures LIMIT, algo theo last, algo theo mark, isolated liquidation, cross liquidation} × {giá chạm, không chạm, chạm rồi quay lại} × {loại A thiếu nến, loại B đủ nến} → trạng thái và thời gian khớp đúng, không khớp hai lần.

**M3. Thứ tự thời gian (I5):** {thanh lý trước giờ funding, sau giờ funding} × {GTD hết hạn trước/sau khi khớp} × {plan hết hạn trước/sau entry} → đúng như Binance.

**M4. Máy trạng thái:** chuyển trạng thái theo ngưỡng, flapping, restart ở từng trạng thái (E1–E3), admin bật/tắt (E13, E14), REST 418 (E6).

**M5. Cách ly (I1):** ArchUnit, và test: trong `PAUSED`, giá OKX khác xa thì `MarketApi.currentLastPrice` vẫn rỗng hoặc là giá Binance cũ, không bao giờ là giá OKX.

**M6. Thông báo:** mỗi người bị ảnh hưởng nhận đúng 1 "tạm dừng" (nếu ≥ 2 phút) và 1 "tổng kết", người không bị ảnh hưởng không nhận gì. Nội dung tổng kết khớp fill/thanh lý/funding thật.

**M7. Bất biến tiền:** chạy lại `FuturesSettlementPropertyTest` và các property test tiền có sẵn với kịch bản có sự cố xen giữa.

**FE:** test component banner theo từng trạng thái, khóa form, nhãn nguồn, poll khi WS rớt; e2e một luồng: đặt LIMIT → admin bật bảo trì → banner + khóa → tắt → RECOVERING → LIVE → thông báo tổng kết.

**Thử thật trên máy:** chặn `fstream.binance.com` bằng file hosts hoặc proxy trong 3 phút, kiểm tra toàn bộ luồng và thời gian khôi phục.

---

## 14. Danh sách task

| # | Việc | Ai | Ước lượng | Phụ thuộc |
|---|---|---|---|---|
| K1 | Ma trận M1–M4 viết trước (đỏ) | BE3 | 1 ngày | — |
| K2 | `market_incident` migration + entity + repository | BE3 | 0.5 ngày | — |
| K3 | Kiểm chứng replay với nến thiếu (E7), E2 mở giao dịch sau replay lúc start, E2b replay mark của vị thế isolated sau restart | BE3 | 1 ngày | — |
| K4 | `MarketHealthMonitor` + `MarketHealthService` + sự kiện + ngưỡng | BE3 | 1.5 ngày | K2 |
| K5 | Cổng `requireTrading` ở mọi service ghi + ArchUnit + mã `TRADING_PAUSED` | BE3 | 1 ngày | K4 |
| K6 | Engine: đóng băng live khi `PAUSED`, quy trình `RECOVERING` (mục 7), nới cửa sổ replay theo sự cố | BE3 | 2 ngày | K4 |
| K7 | Funding/GTD/plan expiry chờ watermark (I5), quyết Q4 | BE3 | 1 ngày | K6 |
| K8 | `GET /market/status`, `/topic/market.status`, API admin bảo trì + audit | BE3 | 1 ngày | K4 |
| K9 | Thông báo in-app tạm dừng và tổng kết, thông báo admin | BE3 (BE2 review module notification) | 1 ngày | K6 |
| K10 | Nguồn dự phòng OKX chỉ để xem + ánh xạ cặp + `source` trong payload + ArchUnit cách ly | BE3 | 2 ngày | K4, Q2 |
| K11 | FE: banner, khóa form, toast, nhãn nguồn, poll, order book ẩn, chart nến dự phòng, PnL "tạm tính" | FE | 2.5 ngày | K8, K10 |
| K12 | FE: trang admin sự cố + nút bảo trì | FE | 1 ngày | K8 |
| K13 | M5–M7, FE test, thử thật bằng chặn host | BE3 + FE | 1 ngày | hết |
| K14 | Cập nhật SRS (MSG mới, use case bảo trì), SDD state machine (PlantUML) | Leader / BE3 | 0.5 ngày | — |

Tổng khoảng **16 ngày công**. Có thể tách 2 PR: **PR 1** (K1–K9, K13 phần BE) là phần quan trọng, an toàn tiền của người dùng; **PR 2** (K10–K12) là giá dự phòng và giao diện. Chỉ PR 1 thôi thì hệ thống vẫn đúng, màn hình chỉ thiếu giá tham khảo.

---

## 15. Quyết định cần chốt

| # | Câu hỏi | Đề xuất |
|---|---|---|
| Q1 | Trong lúc dừng có cho hủy/sửa lệnh không? | **A: chặn** (mục 6.3). B làm sau nếu còn thời gian |
| Q2 | Nguồn dự phòng | **OKX**, Bybit thứ hai; thử truy cập từ region EC2 trước |
| Q3 | Ngưỡng 10s / 30s / 15s / thông báo sau 2 phút | Giữ như mục 4, cho cấu hình |
| Q4 | Funding với vị thế bị thanh lý trong replay | **Đã chốt:** chặn funding tới khi replay mark của cặp qua giờ funding, **và** funding tính theo `source_time` của lệnh đóng thanh lý (mục 7 bước 4). Không thêm cột |
| Q5 | Có hiện nến dự phòng trên chart không? | Có, khác màu, không lưu DB. Hoặc chỉ hiện giá ticker nếu muốn gọn |
| Q6 | Email khi tạm dừng dài? | Không, trừ khi leader muốn (ví dụ sự cố > 1 giờ) |
| Q7 | Trang public `/markets` có hiện banner không? | Có, bản ngắn |

---

## 16. Rủi ro và giới hạn

- Thanh lý trong replay ghi theo thời điểm áp dụng (đã thiết kế từ TR-42). Người dùng sẽ thấy giờ thanh lý là giờ mở lại, không phải giờ giá chạm. Tổng kết cần ghi rõ "giá đã chạm lúc hh:mm".
- Loại A (Binance dừng thật): giá mở lại có thể cách xa giá lúc dừng. Lệnh và thanh lý sẽ xảy ra ngay ở giá mở lại. Đây đúng là hành vi của sàn thật.
- Nguồn dự phòng có giới hạn tần suất. Chỉ bật khi dừng và gom nhiều cặp vào một request.
- Mã chặn phải phủ mọi endpoint ghi; endpoint thêm sau này dễ quên → ArchUnit là lưới an toàn chính.

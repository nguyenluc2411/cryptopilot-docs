*Plan · Module trading · bản nháp để review*

# CryptoPilot Demo Trading: Spot và Futures mô phỏng theo Binance Demo Trading

Kế hoạch chi tiết cho phần giao dịch của Trader: ví ảo, đặt lệnh, khớp lệnh mô phỏng trên giá thật của Binance, vị thế Futures với ký quỹ, thanh lý, funding, lịch sử và phân tích lãi lỗ. Không có lệnh thật, không có API key, không có tiền thật.

- **Ngày:** 06/10/2026
- **Nhánh gốc:** `develop` @ 06c0423
- **Backend:** Java 21 · Spring Boot 4.1 · PostgreSQL/Timescale · Redis
- **Trạng thái:** v5, đã chốt Q-T1 → Q-T10 (Q-T5 sửa: không có reset), Q-T11 team đang bàn. Đã xong TR-02, TR-04 (nhánh `feat/tr-02-paper-trading-schema`, đã push, chờ PR)

## 1. Tóm tắt

Module này là **sàn giao dịch demo độc lập** để người dùng tập trade giống **Binance Demo Trading**. Không dùng tới trading plan: code trading plan hiện có giữ nguyên, không sửa và không phụ thuộc. Phạm vi gồm:

- **Ví ảo** Spot và Futures, chuyển tiền giữa hai ví. Tiền ảo cấp một lần khi mở tài khoản, không có reset.
- **Spot:** Limit, Market, Stop-Limit, OCO, Trailing Stop, Limit kèm TP/SL, Post-only, các chế độ GTC/IOC/FOK.
- **Futures USDⓈ-M:** đòn bẩy theo bracket, Cross/Isolated, One-way/Hedge, Limit/Market/Stop/Take-Profit/Trailing, Reduce-only, TP/SL theo vị thế, thêm/bớt margin, thanh lý, funding fee.
- **Giao diện giống Binance:** chart, order book, giao dịch gần nhất, form đặt lệnh, bảng vị thế/lệnh/lịch sử, phân tích PnL.
- **Điểm riêng của CryptoPilot:** cảnh báo rủi ro theo risk profile ngay trên form đặt lệnh, và gửi thông báo (trong app và push) khi lệnh khớp, TP/SL chạy, margin call, thanh lý, funding.

- `P0` bắt buộc cho bản demo đầu tiên
- `P1` Binance có, cần có trước khi bảo vệ
- `P2` làm nếu còn thời gian
- `Có sẵn` đã có trong code
- `Mở rộng` sửa/mở rộng code đang có
- `Mới` viết mới

## 2. Hiện trạng code liên quan (trên `develop`)

| Thành phần | Đang có | Thiếu cho demo trading |
|---|---|---|
| Trading plan | `TradingPlan` và matching theo plan | **Ngoài phạm vi (Q-T1).** Giữ nguyên, không sửa. Module demo chỉ dùng lại các class tính toán thuần (calculator, warning rule, `PriceLevelBook`). |
| Tính toán rủi ro | `PositionSizeCalculator`, `LiquidationCalculator` (isolated, theo bracket), 8 rule cảnh báo | Chưa có liq price cho Cross và Hedge. Chưa có break-even, margin ratio, max open. |
| Matching engine | `MatchingEngine` + `PriceLevelBook`: chỉ khớp lệnh vào LIMIT theo low/high của nến 1m, một consumer thread cho mỗi partition, replay sau restart bằng `matching_watermark` | Chưa khớp lệnh bán/thoát, Stop, TP, Trailing, OCO. Chưa có phí. Độ trễ tới 1 phút vì chỉ khớp theo nến. |
| Dữ liệu giá | Stream `@kline_*`, Spot `@ticker` (last, bid, ask), Futures `@markPrice@1s` (mark, index, funding, next funding). `CachedPrice` lưu trong Redis. | Chưa có order book (`@depth`), giao dịch gần nhất (`@aggTrade`) và bid/ask của Futures (`@bookTicker`). |
| Cặp giao dịch | `crypto_pair`: tick size, step size, min notional, max leverage. Bảng `leverage_bracket` (MMR, maintenance amount). | Thiếu min/max qty và price band (PERCENT_PRICE) nếu muốn kiểm tra giống Binance (P2). |
| Journal | Có bảng `trading_journal` | Ngoài phạm vi. Module trading chỉ phát event khi vị thế đóng (Q-T9). |
| Realtime | STOMP: `/topic/ticker.*`, `/topic/kline.*`, `/topic/overview.*`, broker có `/queue` | Chưa có kênh riêng cho từng user (lệnh, vị thế, số dư), chưa có topic depth, trades, mark. |
| Gói / quyền | `EntitlementApi`, `futures_analysis`, `active_plan_max` | Cần chốt gói nào được dùng Futures demo. |
| Web / Mobile | Chưa có | Toàn bộ giao diện. |

## 3. Các quyết định

Mỗi mục dưới đây hoặc mâu thuẫn với SRS/quyết định cũ (D-xx, BR-xx), hoặc ảnh hưởng lớn tới thiết kế. Mỗi mục đã có kèm đề xuất của tôi.

#### Q-T1 Quan hệ giữa trading plan và lệnh `Đã chốt`

**Không liên kết với trading plan.** Mục đích là cho người dùng tập trade, nên Trader đặt lệnh trực tiếp như Binance. Module demo trading không đọc, không sửa và không phụ thuộc vào trading plan. Phần cảnh báo rủi ro và thông báo vẫn giữ (mục 9).

#### Q-T2 Margin mode: chỉ Isolated (D-10) hay cả Cross `Đã chốt`

Binance mặc định là Cross. Cross khó hơn: liq price phụ thuộc vào các vị thế khác, cần tính lại mỗi khi bất kỳ mark price nào đổi.

**Đề xuất có cả hai.** Isolated ở giai đoạn 3, Cross ở giai đoạn 4. Cập nhật D-10 trong SRS.

#### Q-T3 Đòn bẩy tối đa `Đã chốt`

Binance cho tới 125x tùy bracket. Risk profile hiện giới hạn 10x và chỉ là WARNING (HIGH_LEVERAGE), không chặn.

**Đề xuất:** cho chọn tới max của bracket giống Binance. Vượt mức của risk profile thì hiện cảnh báo HIGH_LEVERAGE như hiện nay. Đây là điểm khác biệt về giáo dục rủi ro của CryptoPilot.

#### Q-T4 Position mode One-way và Hedge `Đã chốt`

**Đề xuất làm cả hai**, mặc định One-way. Hedge cho phép giữ LONG và SHORT cùng lúc trên một cặp. Chỉ đổi được khi không còn lệnh mở hay vị thế nào (giống Binance).

#### Q-T5 Số dư ảo ban đầu `Đã chốt (sửa 06/10)`

**Cấp một lần khi mở tài khoản, không có reset.** Mặc định Spot 10,000 USDT, 0.1 BTC, 1 ETH, 10 BNB; Futures 5,000 USDT, cấu hình trong `application.yml`. Tài khoản được mở bằng `POST /api/v1/paper/account` khi Trader vào màn giao dịch. Hết tiền là hết, như một tài khoản thật.

#### Q-T6 Mô hình khớp lệnh (độ trễ và độ chính xác) `Đã chốt`

Hiện tại khớp theo nến 1m, nên trễ tới 1 phút và fill được ghi ở thời điểm mở nến. Binance khớp gần như tức thì.

**Đề xuất hai đường.** Đường **live** khớp theo `@aggTrade` và `@bookTicker`, độ trễ dưới 1 giây. Đường **recovery** giữ cơ chế replay nến 1m + watermark hiện có khi stream bị đứt hoặc restart. Cần sửa D-78 (thời điểm fill = thời điểm trade, hoặc thời điểm mở nến nếu là replay).

#### Q-T7 Giá khớp lệnh Market (slippage) `Đã chốt`

**Đề xuất:** khớp dần qua 20 mức giá của order book thật (`@depth20`) để ra giá trung bình VWAP. Nếu không có depth thì khớp ở best bid/ask. Lệnh demo không làm thay đổi sổ lệnh thật; giới hạn này sẽ ghi rõ ở mục 19.

#### Q-T8 Lệnh Limit khớp khi "chạm" hay khi "xuyên qua" giá `Đã chốt`

**Đề xuất:** mặc định khớp khi có trade **xuyên qua** giá (mua: trade < giá đặt; bán: trade > giá đặt), vì như vậy thực tế hơn với lệnh đứng cuối hàng đợi. Nếu trade chỉ chạm đúng bằng giá đặt thì khớp theo tỉ lệ khối lượng (P2). Thêm cấu hình `LIMIT_FILL_MODE = TOUCH | CROSS`. Lưu ý: hiện code đang dùng TOUCH (BR-33), cần sửa BR-33.

#### Q-T9 Ghi journal khi đóng vị thế `Đã chốt`

Journal không thuộc phần trading. Bảng hiện tại còn bắt SIMULATED phải có `plan_id`.

**Đề xuất:** module trading chỉ phát event `PositionClosed` và `SpotRoundTripClosed` (Spring Modulith, cùng cơ chế với các event đang có), kèm đầy đủ entry, exit, PnL, phí, lý do đóng. Người làm journal tự quyết định có nghe event này hay không. Trading không sửa bảng journal.

#### Q-T11 Dữ liệu thị trường đi qua server hay để trình duyệt nối thẳng Binance `Team đang bàn`

Nối thẳng từ trình duyệt tới WebSocket công khai của Binance thì nhanh nhất (bớt một chặng), nhưng giá người dùng thấy có thể lệch với giá server dùng để khớp lệnh, phụ thuộc mạng của người dùng tới Binance, và đi ngược kiến trúc hiện tại (server là nguồn dữ liệu duy nhất, NSF-03).

**Đề xuất: đi qua server**, nhưng tối ưu theo mục 12 để server chỉ thêm dưới 50 ms. Như vậy giá trên màn hình và giá khớp lệnh là một, đúng với một sàn demo.

#### Q-T10 Gói dịch vụ `Đã chốt`

**Đề xuất:** Spot demo dùng được cho mọi gói. Futures demo dành cho gói có `futures_analysis = true`, dùng chung cờ với phân tích Futures và báo lỗi MSG29 như plan hiện tại. Nếu muốn tách quyền riêng thì thêm cột `futures_demo`.

## 4. Tài khoản demo và ví

| Tính năng | Hành vi chi tiết | Ưu tiên | Hiện trạng |
|---|---|---|---|
| Kích hoạt tài khoản demo | Lần đầu Trader vào màn Trading, hệ thống tự tạo demo account và nạp số dư ban đầu (Q-T5). Banner "Demo Trading: tiền ảo, không phải giao dịch thật" luôn hiển thị. | `P0` | `Mới` |
| Ví Spot | Danh sách tài sản gồm: coin, tổng, khả dụng (free), đang khóa trong lệnh (locked), giá trị quy USDT. Có tìm kiếm, ẩn số dư nhỏ (< 1 USDT) và sắp xếp. | `P0` | `Mới` |
| Ví Futures USDⓈ-M | Wallet balance, unrealized PnL, margin balance (= wallet + uPnL), position margin, order margin, available balance, max withdrawable (số tiền chuyển ra được). | `P0` | `Mới` |
| Tổng quan tài sản | Tổng giá trị ước tính theo USDT và BTC, PnL hôm nay (so với snapshot 00:00 UTC), tỉ trọng Spot và Futures. | `P1` | `Mới` |
| Chuyển tiền Spot ↔ Futures | Chuyển USDT (và BNB, nếu cho dùng làm margin; mặc định chỉ USDT). Số chuyển ra khỏi Futures không vượt max withdrawable. Ghi ledger ở cả hai ví trong cùng một transaction. | `P0` | `Mới` |
| Lịch sử chuyển tiền | Danh sách: thời gian, chiều chuyển, tài sản, số lượng. | `P1` | `Mới` |
| Sổ cái (ledger) | Mọi biến động số dư là một dòng bất biến: TRADE, FEE, REALIZED_PNL, FUNDING_FEE, TRANSFER, LIQUIDATION, LIQUIDATION_FEE. Mỗi dòng có `balance_after`. Số dư phải luôn bằng tổng ledger. | `P0` | `Mới` |
| Biểu đồ giá trị tài sản | Snapshot equity hằng ngày lúc 00:00 UTC, biểu đồ 7, 30, 90 ngày. | `P1` | `Mới` |
| Convert số dư nhỏ | Đổi các coin dưới 1 USDT sang USDT theo giá last (giống "Convert small balance"). | `P2` | `Mới` |

## 5. Màn hình giao dịch (dùng chung cho Spot và Futures)

| Tính năng | Hành vi chi tiết | Ưu tiên | Hiện trạng |
|---|---|---|---|
| Chọn cặp | Popup tìm kiếm, tab Yêu thích (dùng watchlist có sẵn) và USDT. Cột: cặp, giá, % 24h, volume. Sắp xếp theo cột. Futures có thêm nhãn "Perp" và đòn bẩy tối đa. | `P0` | `Mở rộng` |
| Thanh ticker 24h | Last price (xanh/đỏ theo tick), thay đổi và % 24h, high, low, volume base/quote. Futures thêm Mark, Index, Funding rate và đếm ngược tới lần funding kế tiếp, Open interest. | `P0` | `Mở rộng` |
| Chart nến, khung tùy chọn | TradingView Lightweight Charts. Người dùng tự chọn khung giống Binance: **1s, 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1D, 3D, 1W, 1M**. Có thanh khung yêu thích và nhớ lựa chọn cho từng user. Kéo chart sang trái thì tải thêm nến cũ (lazy load theo trang 500 nến). Nến đang chạy cập nhật theo từng trade (mục 12). Có thêm volume và các indicator đã có. Futures cho chọn giữa giá Last và Mark. Kiểu chart dạng đường, Heikin-Ashi và công cụ vẽ là P2. | `P0` | `Mở rộng` |
| Hiển thị lệnh và vị thế trên chart | Vẽ đường giá cho lệnh mở, entry của vị thế, TP, SL và liq price. Kéo đường TP/SL để sửa giá (P2), nút ✕ trên đường để hủy lệnh. | `P1` | `Mới` |
| Order book | Bids/asks realtime (20 mức). Gom giá theo bội số tick (ví dụ 0.01 / 0.1 / 1 / 10). Ba chế độ xem: cả hai, chỉ bid, chỉ ask. Last price nằm giữa kèm mũi tên. Thanh tỉ lệ B/S. Click vào một mức giá sẽ điền giá vào form. Thanh nền thể hiện khối lượng tích lũy. | `P0` | `Mới` |
| Depth chart | Biểu đồ độ sâu tích lũy hai phía, dựng từ cùng dữ liệu depth. | `P2` | `Mới` |
| Giao dịch gần nhất (Market trades) | 50 trade gần nhất: giá (xanh = taker mua, đỏ = taker bán), số lượng, thời gian. Cập nhật realtime. | `P0` | `Mới` |
| "My trades" trong panel trades | Tab thứ hai trong panel, chỉ hiện các fill của Trader trên cặp đang xem. | `P1` | `Mới` |
| Panel dưới | Các tab Open orders, Order history, Trade history, Funds (Spot) / Positions, Open orders, Order history, Trade history, Transaction history, Position history (Futures). Có checkbox "Chỉ cặp hiện tại". | `P0` | `Mới` |
| Xác nhận lệnh | Bật/tắt popup xác nhận cho từng loại lệnh (Binance có trong Preferences). | `P2` | `Mới` |
| Bố cục và tùy biến | Ẩn/hiện panel order book, trades, chart. Lưu theo từng user ở localStorage. | `P2` | `Mới` |

> **Lưu ý:** order book và market trades là dữ liệu thật của Binance, chỉ để hiển thị. Lệnh demo của Trader **không** xuất hiện trong sổ lệnh đó.

## 6. Spot

### 6.1 Form đặt lệnh

| Loại lệnh | Hành vi chi tiết | Ưu tiên | Hiện trạng |
|---|---|---|---|
| Limit | Nhập giá và số lượng (hoặc Total). Mặc định GTC. Nếu giá mua ≥ best ask thì khớp ngay như taker ở best ask (được giá tốt hơn), phần còn lại nằm chờ như maker. | `P0` | `Mở rộng` |
| Market | Nhập theo số lượng base ("Amount") hoặc tổng quote ("Total", quoteOrderQty). Khớp theo Q-T7. Hiển thị giá ước tính. | `P0` | `Mở rộng` |
| Stop-Limit | Gồm Stop (trigger, so với last price), Limit và Amount. Khi trigger, lệnh thành Limit. Hướng trigger tự xác định theo vị trí giá hiện tại (giống Binance: STOP_LOSS_LIMIT / TAKE_PROFIT_LIMIT). | `P0` | `Mới` |
| OCO | Một lệnh Limit (TP) và một lệnh Stop-Limit (SL) cùng chiều. Một lệnh khớp hoặc trigger thì lệnh kia bị hủy. Kiểm tra quan hệ giá: bán thì limit > last > stop, mua thì ngược lại. | `P0` | `Mới` |
| Trailing Stop | Trailing delta 0.1%–20% (tính theo BIPS), giá kích hoạt tùy chọn. Theo dõi đỉnh/đáy sau khi kích hoạt và trigger khi giá hồi lại đủ delta. Sau đó thành lệnh Limit/Market. | `P1` | `Mới` |
| Limit kèm TP/SL (OTO / OTOCO) | Tick "TP/SL" trên lệnh Limit mua. Khi lệnh mua khớp sẽ tự đặt OCO bán (TP Limit và SL Stop). | `P0` | `Mới` |
| Post-only (Limit Maker) | Bị từ chối nếu lệnh sẽ khớp ngay khi đặt. | `P1` | `Mới` |
| Time in force | GTC, IOC (khớp được bao nhiêu thì khớp, phần còn lại hủy), FOK (khớp hết hoặc hủy hết). IOC và FOK đánh giá trên depth hiện tại. | `P1` | `Mới` |
| Thanh trượt % và số dư | Slider 0/25/50/75/100% số dư khả dụng. Hiện "Avbl" và "Max buy/sell". Total tự tính và làm tròn theo step size. | `P0` | `Mới` |
| Phí giao dịch | Maker và taker mặc định 0.1% (cấu hình được). Phí trừ vào tài sản **nhận được** (mua BTC thì trừ BTC, bán thì trừ USDT), giống Binance. Hiện phí ước tính ngay trong form. Giảm phí bằng BNB là P2. | `P0` | `Mới` |
| Kiểm tra filter | Giá chia hết tick size, số lượng chia hết step size, giá trị lệnh ≥ min notional, đủ số dư. Thông báo lỗi rõ ràng, giống thông điệp Binance (ví dụ "Order value must be at least 5 USDT"). | `P0` | `Mở rộng` |
| Khóa số dư | Đặt lệnh thì chuyển free → locked (mua khóa quote, bán khóa base). Hủy hoặc hết hạn thì trả lại. Khớp từng phần thì giải phóng tương ứng. | `P0` | `Mới` |
| Cảnh báo rủi ro CryptoPilot | Dùng lại `WarningEvaluator` trên lệnh có SL: risk % vượt risk profile, R:R thấp, SL quá rộng. Chỉ cảnh báo, không chặn. | `P1` | `Mở rộng` |

### 6.2 Quản lý lệnh và tài sản Spot

| Tính năng | Hành vi chi tiết | Ưu tiên | Hiện trạng |
|---|---|---|---|
| Open orders | Cột: thời gian, cặp, loại, chiều, giá, trigger, số lượng, đã khớp %, tổng. Hủy từng lệnh, "Cancel all" (theo cặp hoặc theo loại). OCO hiện thành một nhóm. | `P0` | `Mới` |
| Order history | Trạng thái NEW, PARTIALLY_FILLED, FILLED, CANCELED, EXPIRED, REJECTED. Có giá trung bình. Lọc theo 1 ngày / 1 tuần / 1 tháng / 3 tháng / tùy chọn, theo cặp, chiều, trạng thái. | `P0` | `Mới` |
| Trade history | Từng fill: giá, số lượng, phí và tài sản phí, vai trò Maker/Taker, tổng. | `P0` | `Mới` |
| Hết hạn và hủy tự động | Lệnh của cặp bị tắt (`pair_status = INACTIVE`) thì bị hủy và trả lại số dư. | `P0` | `Mới` |
| Giá vốn và PnL theo coin | Giá vốn trung bình, PnL chưa thực hiện, PnL hôm nay cho từng coin (giống "Spot PnL" của Binance). | `P1` | `Mới` |
| Export CSV | Xuất order, trade và ledger theo khoảng thời gian. | `P2` | `Mới` |

## 7. Futures USDⓈ-M (Perpetual)

### 7.1 Cấu hình

| Tính năng | Hành vi chi tiết | Ưu tiên | Hiện trạng |
|---|---|---|---|
| Đòn bẩy theo cặp | Modal có slider 1x đến max của cặp. Hiện "Maximum position at current leverage" lấy từ `leverage_bracket`. Được đổi khi đang có vị thế nếu margin vẫn đủ: tăng thì luôn được, giảm thì phải kiểm tra margin. Mặc định 20x (Binance mặc định 20x). | `P0` | `Mở rộng` |
| Margin mode theo cặp | Cross hoặc Isolated. Không đổi được khi cặp đó còn vị thế hoặc lệnh mở (Q-T2). | `P0` | `Mở rộng` |
| Position mode | One-way (positionSide = BOTH) hoặc Hedge (LONG và SHORT tách riêng). Áp dụng cho toàn tài khoản, chỉ đổi được khi không còn vị thế và lệnh mở (Q-T4). | `P1` | `Mới` |
| Multi-Assets mode | Không làm (xem mục 10). | – | – |

### 7.2 Form đặt lệnh

| Loại lệnh / tuỳ chọn | Hành vi chi tiết | Ưu tiên | Hiện trạng |
|---|---|---|---|
| Limit | Giá và size. Nút Buy/Long và Sell/Short. Nếu marketable thì phần khớp ngay tính như taker. | `P0` | `Mở rộng` |
| Market | Khớp theo Q-T7. Hiện giá ước tính và liq price ước tính trước khi đặt. | `P0` | `Mở rộng` |
| Stop Limit / Stop Market | Stop price với trigger theo **Mark** hoặc **Last** (working type). Khi trigger, lệnh thành Limit hoặc Market. | `P0` | `Mới` |
| Take Profit Limit / Market | Giống Stop nhưng trigger theo chiều có lời (lệnh TAKE_PROFIT và TAKE_PROFIT_MARKET của Binance). | `P0` | `Mới` |
| Trailing Stop | Callback rate 0.1%–10% (giới hạn cấu hình theo Binance), activation price tùy chọn, trigger theo Mark/Last. Khi trigger thì đặt lệnh Market. | `P1` | `Mới` |
| Post Only (GTX) | Bị từ chối nếu lệnh sẽ khớp ngay. | `P1` | `Mới` |
| Time in force | GTC, IOC, FOK, GTX. | `P1` | `Mới` |
| Reduce-only | Lệnh chỉ được giảm vị thế. Phần vượt quá size vị thế bị hủy hoặc giảm bớt. Khi vị thế đóng hết, các lệnh reduce-only còn lại tự hủy. | `P0` | `Mới` |
| TP/SL kèm lệnh mở | Tick TP/SL: nhập giá TP và SL, chọn trigger Mark/Last. Khi lệnh vào khớp thì tạo hai lệnh TAKE_PROFIT_MARKET và STOP_MARKET với cờ close-position. Hai lệnh này hoạt động kiểu OCO. | `P0` | `Mới` |
| Đơn vị size | Nhập theo coin (BTC) hoặc USDT. Với USDT, chọn theo Cost (margin) hoặc theo Order value (notional), giống tùy chọn của Binance. | `P0` | `Mới` |
| Thông tin trước khi đặt | Cost (margin cần), Max (size tối đa theo số dư và bracket), liq price ước tính, phí ước tính. Panel cảnh báo rủi ro CryptoPilot (đòn bẩy cao, SL vượt liq, funding cao...). | `P0` | `Mở rộng` |
| Kiểm tra | Tick, step, min notional, notional tối đa theo bracket ở mức đòn bẩy đã chọn, đủ available balance, xung đột reduce-only, quan hệ giá stop so với giá hiện tại (Binance báo "Order would immediately trigger"). | `P0` | `Mở rộng` |
| Sửa lệnh Limit | Sửa giá và size của lệnh Limit đang chờ, giữ nguyên ID (Binance Futures hỗ trợ modify order). | `P1` | `Mới` |
| Scaled order | Chia một lệnh thành N lệnh Limit rải đều trong một khoảng giá, phân bổ khối lượng đều, tăng dần hoặc giảm dần. | `P2` | `Mới` |
| Price protection | Không trigger lệnh stop khi Last lệch Mark quá ngưỡng. | `P2` | `Mới` |

### 7.3 Vị thế

| Tính năng | Hành vi chi tiết | Ưu tiên | Hiện trạng |
|---|---|---|---|
| Bảng Positions | Cột: cặp + đòn bẩy + margin mode, Size (xanh/đỏ), Entry price, Break-even price, Mark price, Liq price, Margin ratio, Margin, PnL (ROI %), TP/SL, các nút Close. Cập nhật realtime theo mark price mỗi giây. | `P0` | `Mới` |
| Đóng vị thế | Close bằng Market hoặc Limit (nhập giá, chọn %: 25/50/75/100). Nút "Close all positions" đóng tất cả bằng Market. | `P0` | `Mới` |
| TP/SL cho vị thế | Modal "Entire position" (đóng toàn bộ) hoặc "Partial" (theo size). Trigger theo Mark/Last. Hiện PnL ước tính tại mức TP và SL. | `P0` | `Mới` |
| Thêm/bớt margin (Isolated) | Thêm margin thì liq price xa hơn. Bớt margin chỉ được tới mức còn giữ được initial margin. Hiện liq price mới trước khi xác nhận. | `P0` | `Mới` |
| Cộng dồn vị thế | Mở thêm cùng chiều thì entry tính lại theo giá trung bình gia quyền. One-way: lệnh ngược chiều giảm vị thế, vượt quá thì đảo chiều. | `P0` | `Mới` |
| Đảo vị thế (Reverse) | Một nút đóng vị thế hiện tại và mở vị thế ngược chiều cùng size bằng Market. | `P2` | `Mới` |
| Thẻ chia sẻ PnL | Ảnh PnL/ROI của vị thế để chia sẻ (có thể đăng lên forum). | `P2` | `Mới` |

### 7.4 Cơ chế rủi ro Futures

| Cơ chế | Hành vi chi tiết | Ưu tiên | Hiện trạng |
|---|---|---|---|
| Unrealized PnL | Tính theo **Mark price**: LONG = size × (mark − entry), SHORT = size × (entry − mark). ROI = uPnL / initial margin. | `P0` | `Mới` |
| Margin | Initial margin = notional / đòn bẩy. Maintenance margin = notional × MMR − maintenance amount, lấy theo bracket của notional. | `P0` | `Có sẵn` |
| Liq price Isolated | Đã có công thức cho one-way. Cần thêm Hedge và tính lại khi thêm/bớt margin hoặc cộng dồn vị thế. | `P0` | `Mở rộng` |
| Liq price Cross | Theo công thức Binance: wallet balance trừ maintenance margin và cộng uPnL của **các vị thế cross khác**. Tính lại khi có mark price mới của bất kỳ cặp nào đang có vị thế. | `P0` | `Mới` |
| Margin ratio và margin call | Margin ratio = maintenance margin / margin balance. Từ 80% trở lên thì gửi thông báo margin call. Tới 100% thì thanh lý. | `P0` | `Mới` |
| Liquidation engine | Kiểm tra theo từng tick mark price, có "sổ" liq price theo cặp giống `PriceLevelBook`. Khi thanh lý: hủy lệnh mở của cặp (isolated) hoặc toàn bộ lệnh (cross), đóng vị thế ở giá mark, trừ liquidation clearance fee (tỉ lệ cấu hình), ghi ledger và journal với `close_reason = LIQUIDATION`. | `P0` | `Mới` |
| Funding fee | Tại mỗi `nextFundingTime` (8h/4h/1h tùy cặp, lấy từ stream): phí = size × mark × funding rate. Rate dương thì LONG trả, SHORT nhận. Idempotent theo (vị thế, thời điểm funding). Dữ liệu `FundingSettlement` đã có. | `P0` | `Mở rộng` |
| Phí giao dịch | Maker 0.02%, taker 0.05% trên notional (mức thường của Binance, cấu hình được). Trừ vào wallet balance. | `P0` | `Mới` |
| Break-even price | Entry đã điều chỉnh theo phí mở và phí đóng ước tính (taker). | `P1` | `Mới` |
| ADL, insurance fund | Không mô phỏng (mục 10). Đèn ADL trên UI luôn ẩn. | – | – |

### 7.5 Công cụ tính (Calculator)

Modal giống Binance gồm 5 tab: **PnL**, **Target price**, **Liquidation price**, **Max open**, **Open price** (giá trung bình nhiều lệnh). Phần lõi tính toán dùng lại `PositionSizeCalculator` và `LiquidationCalculator` qua endpoint không lưu dữ liệu (giống `/plans/calculate`). `P1` `Mở rộng`

## 8. Lịch sử giao dịch và phân tích PnL

> **Lịch sử giao dịch luôn được lưu**, và đây là phần của trading. Mỗi lệnh, mỗi lần khớp, mỗi vị thế và mỗi biến động số dư đều ghi vào database (các bảng `paper_order`, `paper_fill`, `paper_position`, `paper_ledger_entry` ở mục 14). Dữ liệu chỉ thêm vào, không bao giờ xoá. Riêng **journal** (Trader tự ghi setup, bài học, lỗi sai) mới là phần ngoài phạm vi.

| Tính năng | Hành vi chi tiết | Ưu tiên | Hiện trạng |
|---|---|---|---|
| Spot: Order history / Trade history | Xem mục 6.2: mọi lệnh (kể cả lệnh đã hủy hay bị từ chối) và mọi lần khớp, có giá, phí, Maker/Taker. | `P0` | `Mới` |
| Futures: Order history / Trade history | Giống Spot, thêm Realized PnL trên từng fill và positionSide. | `P0` | `Mới` |
| Futures: Transaction history | Lọc theo loại: Realized PnL, Commission, Funding fee, Transfer, Liquidation fee. Đọc từ ledger. | `P0` | `Mới` |
| Futures: Position history | Vị thế đã đóng: mở/đóng lúc nào, entry trung bình, close trung bình, size max, realized PnL (đã trừ phí và funding), lý do đóng. | `P0` | `Mới` |
| Bộ lọc và tra cứu | Lọc theo khoảng thời gian (1 ngày, 1 tuần, 1 tháng, 3 tháng, tùy chọn), theo cặp, chiều, loại lệnh, trạng thái, phiên demo. Phân trang theo cursor để trang sau vẫn nhanh khi lịch sử dài. Xem chi tiết một lệnh gồm toàn bộ các lần khớp của nó. | `P0` | `Mới` |
| Lưu trữ | Giữ vĩnh viễn, không bao giờ xoá. Có index theo (account, thời gian) và có thể chuyển `paper_fill`, `paper_ledger_entry` thành hypertable Timescale khi dữ liệu lớn. | `P0` | `Mới` |
| Export CSV | Xuất lịch sử lệnh, lịch sử khớp, transaction history theo khoảng thời gian (Binance cho xuất báo cáo). | `P1` | `Mới` |
| PnL Analysis | Tách theo Spot và Futures, kỳ 7/30/90 ngày. Gồm: PnL hôm nay, PnL tích lũy (line), PnL ngày (bar xanh/đỏ), lịch PnL theo tháng, win rate, số lệnh thắng/thua, lời/lỗ trung bình, profit factor, max drawdown. | `P1` | `Mới` |
| Event vị thế đóng | Phát `PositionClosed` và `SpotRoundTripClosed` để module khác (journal, thống kê) dùng nếu cần (Q-T9). | `P1` | `Mới` |

## 9. Cảnh báo, thông báo, admin

| Tính năng | Hành vi chi tiết | Ưu tiên | Hiện trạng |
|---|---|---|---|
| Thông báo realtime | Toast trên web qua `/user/queue/*` khi: lệnh khớp/khớp một phần, lệnh stop/TP trigger, lệnh bị hủy do hệ thống, margin call, thanh lý, funding đã thanh toán. | `P0` | `Mới` |
| Thông báo lưu và push | Ghi vào bảng `notification` có sẵn. Push FCM cho mobile, tôn trọng notification preferences của user. | `P1` | `Mở rộng` |
| Cảnh báo rủi ro khi đặt lệnh | Panel cảnh báo ngay trên form, tính lại mỗi khi Trader sửa giá/size/đòn bẩy. Dùng các rule đã có: đòn bẩy vượt risk profile, risk % quá lớn so với vốn, R:R thấp (khi có TP/SL), SL vượt liq price, SL quá rộng, funding cao, tổng rủi ro mở quá lớn, không đủ vốn. Mức BLOCKING (không đủ vốn, SL vượt liq) chặn đặt lệnh; các mức khác chỉ cảnh báo và cho đặt tiếp. Không đặt SL thì hiện nhắc "Lệnh chưa có Stop Loss". | `P0` | `Mở rộng` |
| Cảnh báo khi đang giữ vị thế | Gửi thông báo khi: margin ratio vượt 50% / 80%, giá mark cách liq price dưới 5%, funding sắp trừ lớn (trước 15 phút), vị thế không có SL quá X giờ (cấu hình). Mỗi loại có cooldown để không spam. | `P1` | `Mới` |
| Admin: cấu hình | Phí maker/taker Spot và Futures, số dư ban đầu, liquidation fee, LIMIT_FILL_MODE, bật/tắt demo trading cho từng cặp. | `P1` | `Mở rộng` |
| Admin: giám sát | Số tài khoản demo, số lệnh mở, số vị thế, độ trễ matching, trạng thái stream, các lần thanh lý gần nhất. Mọi thao tác admin ghi audit log. | `P2` | `Mở rộng` |

## 10. Ngoài phạm vi (đề xuất **không** làm)

Các mục dưới đây có trên Binance nhưng nằm ngoài màn Spot / USDⓈ-M Futures hoặc không có ý nghĩa khi mô phỏng. Nếu bạn muốn làm mục nào thì đánh dấu lại.

| Tính năng Binance | Lý do không làm |
|---|---|
| Nạp/rút, P2P, Buy Crypto | Không có tiền thật (README đã cam kết). |
| COIN-M Futures, Options | Sản phẩm khác, công thức margin khác. Có thể làm phiên bản sau. |
| Margin trading (Spot cross/isolated margin, vay) | Cần mô phỏng lãi vay và thanh lý riêng, làm tăng phạm vi đáng kể. |
| Multi-Assets mode, Portfolio Margin | Cần haircut và tỉ giá chéo giữa nhiều tài sản margin. |
| Trading bots (Grid, DCA), Copy trading | Là sản phẩm riêng của Binance. Có thể là hướng mở rộng sau. |
| TWAP / algo orders | P2+, ít giá trị cho học tập. |
| ADL, insurance fund, VIP tier, giảm phí BNB | Phụ thuộc thanh khoản và người dùng thật của sàn. |
| Convert, Earn, Launchpool | Không phải chức năng giao dịch. |
| API trading cho user | CryptoPilot không cấp API key. |

## 11. Luật mô phỏng khớp lệnh

### 11.1 Nguồn giá

| Dữ liệu | Stream Binance | Dùng để | Hiện trạng |
|---|---|---|---|
| Best bid/ask | <s>@bookTicker | Khớp Market, IOC/FOK, kiểm tra lệnh marketable và post-only | `Mới` |
| Trade | <s>@aggTrade | Khớp Limit đang chờ, trigger Stop/TP/Trailing theo Last, panel market trades | `Mới` |
| Order book | <s>@depth20@100ms | VWAP cho lệnh Market (Q-T7), panel order book. **Chỉ subscribe cho cặp đang có người xem** hoặc có lệnh chờ, để giữ trong giới hạn stream. | `Mới` |
| Mark/Index/Funding | <s>@markPrice@1s | uPnL, liquidation, trigger theo Mark, funding | `Có sẵn` |
| Nến 1m | <s>@kline_1m + REST | Recovery: replay từ watermark sau khi restart hoặc mất stream | `Có sẵn` |

### 11.2 Quy tắc khớp

| Trường hợp | Quy tắc | Vai trò phí |
|---|---|---|
| Market mua / bán | Đi dần qua các mức ask (mua) hoặc bid (bán) của depth20 tới khi đủ số lượng, giá khớp = VWAP. Nếu depth không đủ thì phần còn lại khớp ở mức giá cuối, gắn cờ `depth_exhausted`. Không có depth thì khớp ở best ask/bid. | Taker |
| Limit marketable khi đặt | Khớp ngay như Market nhưng không vượt quá giá limit. Phần chưa khớp nằm chờ (GTC), bị hủy (IOC), hoặc hủy toàn bộ (FOK, nếu không khớp đủ). | Taker rồi Maker |
| Limit đang chờ | Mua khớp ở giá limit khi có aggTrade với giá < limit (CROSS) hoặc ≤ limit (TOUCH), theo Q-T8. Bán thì ngược lại. Khớp hết một lần (khớp một phần theo khối lượng trade là P2). | Maker |
| Stop / TP (trigger) | Spot so với Last. Futures so với Mark hoặc Last theo working type. Khi điều kiện đạt, lệnh chuyển thành Limit/Market và đi qua các quy tắc trên. Trạng thái ghi lại `triggered_at`. | Theo lệnh con |
| Trailing | Sau khi giá chạm activation price (hoặc ngay lúc đặt nếu bỏ trống), ghi đỉnh (lệnh bán) hoặc đáy (lệnh mua). Trigger khi giá hồi lại ≥ callback rate. | Taker |
| OCO / OTOCO | Các lệnh thuộc cùng một `order_list`. Một lệnh khớp hoặc trigger thì hủy các lệnh còn lại trong cùng transaction. | – |
| Thứ tự trong cùng một tick | Thanh lý trước, sau đó tới TP/SL của vị thế, rồi tới các lệnh khác theo thời gian đặt. Có quy tắc cố định để kết quả replay luôn giống nhau. | – |
| Lệnh đặt sau khi giá đã chạy qua | Giữ nguyên D-77: một trade hoặc nến xảy ra trước thời điểm đặt lệnh thì không được dùng để khớp lệnh đó. | – |

### 11.3 Kiến trúc engine

- **Engine riêng cho demo trading:** viết engine mới cho lệnh demo (`RestingOrder`), dùng lại `PriceLevelBook` và cách làm của `MatchingEngine`. Engine khớp theo plan hiện tại giữ nguyên chạy song song, không sửa. Mỗi (market, pair) có 4 sổ: limit mua, limit bán, trigger lên, trigger xuống, cộng thêm sổ liq price của vị thế. Vẫn một consumer thread cho mỗi partition, không cần lock (giữ ADR-011).
- **Ghi kết quả:** mỗi fill được xử lý trong một transaction: cập nhật lệnh (compare-and-set theo trạng thái như `executeIfActive`), fill, số dư, vị thế, ledger. Sau đó publish event cho user queue.
- **Đồng bộ tài khoản:** thao tác của user (đặt, hủy, chuyển tiền) và fill của engine cùng sửa số dư. Khóa theo account bằng `pg_advisory_xact_lock(hash(account_id))` kết hợp optimistic `version`.
- **Cross margin:** mark price mới của cặp X sẽ tính lại margin ratio của mọi account có vị thế cross ở X. Có index theo cặp, chỉ quét account liên quan.
- **Funding job:** `@Scheduled` chạy theo `nextFundingTime`, khóa Redis lease giống replay lock (R-09) để chỉ một instance chạy. Ghi theo unique key để chạy lại không bị trừ hai lần.
- **Snapshot equity hằng ngày:** job 00:00 UTC.

## 12. Realtime độ trễ thấp (Binance → server → web)

### 12.1 Hiện tại chậm ở đâu

| Chặng | Hiện tại | Độ trễ thêm vào |
|---|---|---|
| Nguồn Binance | Spot dùng `@ticker` (Binance đẩy mỗi 1s) và `@kline_*` (Spot đẩy mỗi 2s). Futures dùng `@markPrice@1s`. | 1 – 2 s |
| Server gom tin | `MarketBroadcastServiceImpl` gom tin rồi `MarketHubJob` đẩy theo nhịp cố định `updateInterval = 1s`, overview 2s. Mục tiêu SRS 4.2.3 hiện chỉ là "dưới 2s". | 0 – 1 s |
| Khung nến | Chỉ stream 1m, 15m, 1h, 4h, 1d. Mỗi khung là một stream riêng cho mỗi cặp. | – |
| **Tổng** | Giá trên web có thể trễ tới 2–3 giây so với Binance. Như vậy là đủ cho màn phân tích, nhưng quá chậm cho màn giao dịch. | **≤ 3 s** |

### 12.2 Mục tiêu

| Chỉ số | Mục tiêu (p95) | Đo bằng |
|---|---|---|
| Server thêm vào (nhận từ Binance tới khi gửi ra socket) | < 50 ms | Micrometer timer trên server |
| Đầu cuối (event time Binance tới lúc trình duyệt vẽ), người dùng ở Việt Nam | < 300 ms | Client gửi mẫu đo về `/api/v1/metrics/latency` |
| Fill demo tới lúc user thấy lệnh khớp | < 500 ms | Từ trade time tới khi nhận tin trên `/user/queue/fills` |

### 12.3 Cách làm

| Hạng mục | Thay đổi | Ưu tiên |
|---|---|---|
| Nguồn nhanh nhất của Binance | Màn giao dịch dùng các stream realtime: `@aggTrade` (đẩy theo từng trade), `@bookTicker` (đẩy ngay khi best bid/ask đổi), `@depth20@100ms`, Futures `@markPrice@1s`. Giữ `@ticker` cho số liệu 24h. | `P0` |
| Đẩy theo sự kiện, không theo nhịp 1s | Các topic của màn giao dịch (trades, book, depth, nến đang chạy) gửi ngay khi có tin. Chỉ gom trong cửa sổ nhỏ (mặc định 50–100 ms) để không vượt quá tốc độ vẽ của trình duyệt. Trades gửi theo lô các trade mới, depth gửi bản mới nhất. Overview và màn phân tích giữ nhịp cũ. | `P0` |
| Chỉ gửi cho topic có người xem | Theo dõi số người subscribe từng topic (`SessionSubscribeEvent` / `SessionUnsubscribeEvent`). Topic không ai xem thì không tạo payload và không gửi. Depth20 chỉ subscribe Binance cho cặp đang có người xem (nhả ra sau 60s không còn ai). | `P0` |
| Nến đang chạy dựng từ trade | Mỗi cặp chỉ cần **một** stream `@aggTrade`. Server cập nhật nến đang chạy của **mọi** khung (1s tới 1M) ngay trên mỗi trade và đẩy cho khung đang có người xem. Khi nến đóng, đối chiếu với kline chính thức của Binance (1m) và gửi bản chuẩn để sửa nếu lệch. | `P0` |
| Lịch sử nến cho mọi khung | Khung đã lưu DB (1m, 15m, 1h, 4h, 1d) đọc từ `ohlcv`. Khung khác (1s, 3m, 5m, 30m, 2h, 6h, 8h, 12h, 3D, 1W, 1M) gộp từ khung nhỏ hơn đã lưu, hoặc gọi REST Binance `/klines` rồi cache Redis (TTL ngắn), có `BinanceRequestGate` giữ trong giới hạn rate. 1s chỉ giữ trong bộ nhớ khoảng 1 giờ gần nhất. | `P0` |
| Snapshot ban đầu rồi mới tới cập nhật | Mở màn hình: REST trả snapshot (nến, depth, 50 trade) kèm `lastUpdateId` / thời điểm. Client subscribe trước, lưu tạm tin tới, rồi ghép với snapshot theo id để không mất tin và không nhấp nháy. | `P0` |
| Payload gọn | Serialize JSON một lần cho mỗi topic rồi gửi cho mọi subscriber. Tên trường ngắn, số dạng chuỗi giống Binance (giữ đủ chữ số). Có thể bật nén permessage-deflate sau khi đo. | `P1` |
| Không chặn luồng đọc stream | Luồng đọc WebSocket Binance chỉ parse rồi đưa vào hàng đợi. Matching, broadcast và cache chạy ở các consumer riêng, nên một bên chậm không kéo bên kia. Session web nào chậm thì bỏ bớt tin cũ của session đó (đã có giới hạn buffer). | `P0` |
| Vị trí đặt server | Server Binance đặt ở AWS Tokyo. Deploy server ở Tokyo hoặc Singapore để chặng Binance → server chỉ vài chục ms, và server → Việt Nam khoảng 30–80 ms. Tránh đặt server ở Mỹ/EU. | `P1` |
| Phía web vẽ nhanh | Dữ liệu realtime để ngoài React state (store + ref), vẽ gộp theo `requestAnimationFrame`, chart cập nhật bằng `series.update()` chứ không vẽ lại toàn bộ. Order book chỉ sửa các dòng đổi. Parse tin trong Web Worker nếu tần suất cao. Tab bị ẩn thì tạm dừng vẽ. | `P0` |
| Đo và hiển thị độ trễ | Mỗi tin mang event time của Binance (`E`) và thời điểm server gửi. Server ghi histogram độ trễ từng chặng. Web hiện chấm trạng thái kết nối kèm độ trễ (xanh < 300 ms, vàng < 1 s, đỏ hoặc mất kết nối), tự kết nối lại và lấy snapshot mới. | `P1` |
| Nhiều instance (sau này) | Simple broker trong bộ nhớ đủ cho một instance. Khi chạy nhiều instance thì chuyển sang STOMP broker relay (RabbitMQ) hoặc Redis pub/sub. | `P2` |

> Thay đổi này cũng làm nhanh màn phân tích thị trường đang có, nhưng phải cập nhật SRS 4.2.3 và TECHNICAL_DESIGN 9 (hiện quy định nhịp 1s/2s) cho màn giao dịch.

## 13. Ví dụ tính toán (dùng làm test case)

Số liệu dưới đây chỉ là ví dụ minh họa. MMR và phí thật lấy theo bảng `leverage_bracket` và cấu hình.

#### Spot · Mua 0.01 BTC Limit 60,000

```
Khóa:     0.01 × 60,000        = 600 USDT
Khớp (maker 0.1%)
Nhận:     0.01 − 0.01×0.1%     = 0.00999 BTC
Trừ:      600 USDT (từ locked)
Ledger:   TRADE −600 USDT, TRADE +0.01 BTC,
          FEE −0.00001 BTC
```

#### Futures · Long 0.1 BTC, 10x Isolated

```
Entry 60,000 (Market, taker 0.05%)
Notional = 0.1 × 60,000         = 6,000
IM       = 6,000 / 10           = 600
Phí mở   = 6,000 × 0.05%        = 3
MMR 0.4%, maint. amount 0 (ví dụ)
Liq = (6,000 − 600 − 0) / (0.1 × (1 − 0.004))
    = 5,400 / 0.0996            ≈ 54,216.87
```

#### Futures · uPnL và funding

```
Mark 61,000:
uPnL  = 0.1 × (61,000 − 60,000) = +100
ROI   = 100 / 600               = +16.67%
Funding rate +0.01% tại mark 61,000:
Long trả 0.1 × 61,000 × 0.01%   = 0.61 USDT
```

#### Futures · Short đóng bởi SL

```
Short 1 ETH @ 3,000, 5x, SL STOP_MARKET 3,150 (Mark)
Mark chạm 3,150 → Market mua 1 ETH
Giả sử VWAP 3,151.2 (taker 0.05%)
Realized = 1 × (3,000 − 3,151.2) = −151.2
Phí      = 3,000×0.05% + 3,151.2×0.05% = 3.08
close_reason = STOP_LOSS → ghi journal
```

## 14. Mô hình dữ liệu (migration V21)

Đã hiện thực ở `V21__paper_trading.sql`. Tên bảng có tiền tố `paper_` để không lẫn với dữ liệu demo hiện có (`R__demo_dataset.sql`). Thêm bảng `paper_transfer` cho lịch sử chuyển tiền.

| Bảng | Cột chính | Ràng buộc quan trọng |
|---|---|---|
| paper_account | account_id, user_id (unique), position_mode (ONE_WAY/HEDGE), version | Mỗi user một account |
| paper_balance | account_id, wallet (SPOT/FUTURES), asset, free, locked, version | PK (account, wallet, asset); free ≥ 0, locked ≥ 0 |
| paper_futures_setting | account_id, pair_id, leverage, margin_mode (CROSS/ISOLATED) | leverage trong khoảng 1..max của cặp |
| paper_order_list | list_id, account_id, type (OCO/OTO/OTOCO), status | Nhóm các lệnh liên quan |
| paper_order | order_id, client_order_id, account_id, market, pair_id, side (BUY/SELL), position_side (BOTH/LONG/SHORT), type, time_in_force, price, stop_price, working_type (MARK/LAST), activation_price, callback_rate, orig_qty, quote_order_qty, executed_qty, cum_quote, avg_price, reduce_only, close_position, post_only, status, list_id, parent_order_id, reject_reason, triggered_at, created_at, updated_at, version | CHECK theo type: LIMIT bắt buộc có price; STOP* bắt buộc có stop_price; Spot không có position_side/reduce_only. Index partial cho lệnh đang mở. |
| paper_fill | fill_id, order_id, account_id, price, qty, quote_qty, fee, fee_asset, is_maker, realized_pnl, source (LIVE/REPLAY), trade_time | Bất biến, dạng append-only |
| paper_position | position_id, account_id, pair_id, position_side, margin_mode, leverage, qty, entry_price, isolated_margin, realized_pnl, cum_fee, cum_funding, max_qty, opened_at, closed_at, close_reason, version | Tối đa 1 vị thế mở cho mỗi (account, pair, position_side). Đóng hẳn thì chuyển sang lịch sử (closed_at khác null). |
| paper_ledger_entry | entry_id, account_id, wallet, asset, type, amount, balance_after, ref_type, ref_id, created_at | Append-only. Có thể làm hypertable nếu dữ liệu lớn. |
| paper_funding_payment | account_id, position_id, funding_time, rate, mark_price, amount | Unique (position_id, funding_time) để tránh trừ hai lần |
| paper_equity_snapshot | account_id, day, spot_value, futures_value, total_usdt | PK (account, day) |
| paper_matching_watermark | market_type, pair_id, last_candle_open_time | Watermark riêng cho engine demo, tách khỏi `matching_watermark` của plan |

Toàn bộ dùng `numeric(28,12)` cho giá/số lượng và `numeric(28,8)` cho tiền, đúng quy ước hiện có. Làm tròn: giá theo tick (lệnh mua làm tròn xuống, liq price làm tròn lên như code hiện tại), số lượng theo step (luôn làm tròn xuống), phí làm tròn tới 8 chữ số thập phân.

## 15. API và kênh realtime

### 14.1 REST (`/api/v1/paper`, Trader)

| Method · Path | Mô tả |
|---|---|
| GET · /account | Account, position mode, session (tự tạo nếu chưa có) |
| POST · /account | Mở tài khoản và cấp tiền ảo một lần (idempotent: 201 lần đầu, 200 các lần sau). Các GET chỉ đọc, trả 404 khi chưa mở. |
| GET · /wallets/{spot\|futures} | Số dư, tổng hợp margin |
| POST · /transfers · GET /transfers | Chuyển tiền Spot ↔ Futures và lịch sử |
| GET · /ledger | Sổ cái, lọc theo wallet, type, from, to, có phân trang |
| POST · /spot/orders | Đặt lệnh đơn |
| POST · /spot/order-lists | OCO / OTO / OTOCO |
| DELETE · /spot/orders/{id} · /spot/orders?pairId= | Hủy một lệnh / hủy tất cả |
| GET · /spot/orders/open · /spot/orders · /spot/fills | Lệnh mở, lịch sử lệnh, lịch sử khớp |
| GET/PUT · /futures/pairs/{pairId}/setting | Đòn bẩy, margin mode |
| PUT · /futures/position-mode | One-way / Hedge |
| POST · /futures/orders · PUT /futures/orders/{id} | Đặt lệnh (có thể kèm TP/SL) / sửa lệnh Limit |
| DELETE · /futures/orders/{id} · /futures/orders?pairId= | Hủy |
| GET · /futures/positions | Vị thế đang mở |
| POST · /futures/positions/{id}/close · /futures/positions/close-all | Đóng Market/Limit, theo % |
| PUT · /futures/positions/{id}/tpsl | TP/SL cho vị thế |
| POST · /futures/positions/{id}/margin | Thêm/bớt margin isolated |
| GET · /futures/orders · /futures/fills · /futures/positions/history · /futures/income | Lịch sử lệnh, khớp, vị thế, giao dịch |
| POST · /futures/calculator/{pnl\|target\|liquidation\|max-open\|open-price} | Calculator, không lưu dữ liệu |
| GET · /pnl/summary · /pnl/daily | Phân tích PnL |
| GET · /api/v1/market/{market}/{symbol}/depth · /trades | Snapshot ban đầu cho order book và trades (public) |

Lỗi trả về theo problem detail chuẩn đang dùng. Bổ sung mã lỗi: `INSUFFICIENT_BALANCE`, `MIN_NOTIONAL`, `PRICE_FILTER`, `LOT_SIZE`, `WOULD_IMMEDIATELY_TRIGGER`, `WOULD_TAKE` (post-only), `REDUCE_ONLY_REJECTED`, `MAX_NOTIONAL_AT_LEVERAGE`, `HAS_OPEN_POSITION_OR_ORDER`. Đặt lệnh nhận header `Idempotency-Key` (hoặc `clientOrderId`) để tránh double-submit.

### 14.2 STOMP

| Đích | Nội dung |
|---|---|
| /topic/depth.{market}.{symbol} | Order book 20 mức (public; cập nhật regex `PUBLIC_TOPICS`) |
| /topic/trades.{market}.{symbol} | Market trades (public) |
| /topic/mark.{symbol} | Mark, index, funding, countdown (public) |
| /user/queue/orders | Thay đổi trạng thái lệnh |
| /user/queue/fills | Fill mới |
| /user/queue/positions | Vị thế mở/đổi/đóng. uPnL do client tự tính từ mark để giảm tải server |
| /user/queue/balances | Số dư thay đổi |
| /user/queue/alerts | Margin call, thanh lý, funding |

## 16. Màn hình web (React + Vite)

| Màn / modal | Thành phần | Ưu tiên |
|---|---|---|
| Spot Trade | Ticker bar · Chart · Order book · Trades · Form Buy/Sell (tab Limit / Market / Stop-Limit / OCO / Trailing) · Panel dưới | `P0` |
| Futures Trade | Như Spot, thêm: Margin mode · Đòn bẩy · Funding countdown · Form có TP/SL, reduce-only, TIF · Margin ratio của tài khoản · Panel Positions | `P0` |
| Wallet Overview / Spot / Futures | Tổng tài sản, danh sách tài sản, nút Transfer | `P0` |
| Orders | Trang riêng gồm open orders và toàn bộ lịch sử, bộ lọc, phân trang | `P0` |
| PnL Analysis | Thẻ tổng hợp, PnL tích lũy, PnL ngày, lịch, thống kê | `P1` |
| Modal | Transfer · Leverage · Margin mode · Position mode · TP/SL vị thế · Close Limit · Thêm/bớt margin · Calculator · Xác nhận lệnh | `P0` |
| Mobile (Flutter) | Bố cục rút gọn: form + order book cạnh nhau, chart ở tab riêng, có các panel vị thế/lệnh. Làm sau khi web xong. | `P1` |

Thư viện gợi ý: TradingView **Lightweight Charts** cho chart, `@stomp/stompjs` cho realtime, TanStack Query cho REST. Mọi phép tính số trên client dùng `decimal.js`, không dùng `number`.

## 17. Lộ trình và danh sách task

Ước lượng theo ngày công của 1 dev backend. Frontend làm song song từ giai đoạn 2. Mốc dự kiến tính từ 07/10/2026 và để dư thời gian trước khi kết thúc capstone (03/2027).

### **GĐ 0**07–13/10 — Chốt thiết kế và dữ liệu nền

- **TR-01** Chốt Q-T2…Q-T10, viết BR mới cho demo trading (không sửa BR của plan) · 1d
- `Xong` **TR-02** Migration: paper_account, paper_balance, paper_ledger_entry, paper_order, order_list, paper_fill, paper_futures_setting, paper_position, paper_funding_payment, paper_equity_snapshot, paper_matching_watermark · 2d
- **TR-03** Stream `@bookTicker`, `@aggTrade`, `@depth20` (subscribe theo nhu cầu), cache Redis, topic public · 3d

### **GĐ 1**14/10–03/11 — Ví và Spot cơ bản

- `Xong` **TR-04** Demo account, số dư ban đầu, ví Spot/Futures, ledger, chuyển tiền · 3d
- **TR-05** Engine khớp lệnh demo (`RestingOrder`, dùng lại `PriceLevelBook`), đường live và recovery · 4d
- **TR-06** Spot Limit/Market: kiểm tra filter, khóa số dư, VWAP depth, phí, hủy / hủy tất cả · 4d
- **TR-07** Open orders, order history, fill history API · 2d
- **TR-08** User queue STOMP (orders, fills, balances) · 2d
- **TR-34** Realtime độ trễ thấp: đẩy theo sự kiện, đếm subscriber theo topic, hàng đợi tách luồng đọc stream, snapshot kèm id · 4d
- **TR-35** Nến đang chạy dựng từ aggTrade cho mọi khung, lịch sử nến 16 khung (gộp từ DB hoặc REST + cache) · 4d
- **TR-36** Đo độ trễ (Micrometer, mẫu đo từ client) · 1d

### **GĐ 2**04–17/11 — Spot nâng cao

- **TR-09** Stop-Limit, trigger theo Last · 2d
- **TR-10** OCO, OTO, OTOCO (order_list) · 3d
- **TR-11** Trailing Stop · 2d
- **TR-12** TIF IOC/FOK, Post-only · 2d
- **TR-13** Giá vốn trung bình và PnL theo coin, equity snapshot · 2d

### **GĐ 3**18/11–08/12 — Futures cốt lõi (Isolated)

- **TR-14** Cài đặt đòn bẩy và margin mode, position mode One-way/Hedge · 2d
- **TR-15** Futures Limit/Market, kiểm tra notional tối đa theo bracket, phí · 3d
- **TR-16** Vị thế: mở, cộng dồn, giảm, đảo chiều; entry trung bình; realized PnL; reduce-only · 4d
- **TR-17** Đóng Market/Limit, close-all, thêm/bớt margin isolated · 2d
- **TR-18** Liq price isolated cho Hedge, break-even, margin ratio · 2d
- **TR-19** Lịch sử lệnh, fill, vị thế, income · 2d

### **GĐ 4**09/12–05/01 — Rủi ro Futures và lệnh điều kiện

- **TR-20** Stop/TP Limit/Market theo Mark/Last, TP/SL kèm lệnh, TP/SL vị thế · 4d
- **TR-21** Trailing Stop Futures · 1d
- **TR-22** Liquidation engine (isolated) và margin call · 3d
- **TR-23** Cross margin: liq price, liquidation, tính lại khi mark đổi · 4d
- **TR-24** Funding job idempotent · 2d
- **TR-25** Sửa lệnh Limit, Calculator 5 tab · 2d

### **GĐ 5**06–23/01 — Cảnh báo, thông báo, phân tích

- **TR-26** Panel cảnh báo rủi ro cho lệnh Spot/Futures (dùng lại rule có sẵn), chặn mức BLOCKING · 3d
- **TR-27** Cảnh báo khi giữ vị thế (margin ratio, gần liq, funding, thiếu SL) có cooldown; phát event vị thế đóng · 3d
- **TR-28** PnL analysis API · 3d
- **TR-29** Notification lưu bảng, FCM, tôn trọng preferences · 2d
- **TR-30** Admin config và giám sát, audit · 2d

### **GĐ 6**song song — Frontend web (dev FE)

- **TR-F1** Khung layout trading, chọn cặp, ticker bar, chart (từ GĐ 1)
- **TR-F2** Order book, trades, depth, chọn khung nến, vẽ theo requestAnimationFrame, chấm trạng thái độ trễ (sau TR-03, TR-34)
- **TR-F3** Form Spot, panel lệnh, ví, transfer (sau TR-06)
- **TR-F4** Form Futures, positions, các modal (sau TR-16)
- **TR-F5** Vẽ lệnh và vị thế trên chart, PnL analysis, calculator

### **GĐ 7**26/01–13/02 — Ổn định và nghiệm thu

- **TR-31** Test restart/replay, mất stream, double-submit, race giữa hủy và khớp · 3d
- **TR-32** Load test: 500 account × 20 lệnh chờ, độ trễ đầu cuối p95 < 300 ms, fill p95 dưới 1s · 2d
- **TR-33** OpenAPI, tài liệu, dữ liệu demo cho buổi bảo vệ (mở rộng `R__demo_dataset.sql`) · 2d

Tổng backend khoảng **~92 ngày công**. Nếu chỉ có một người làm backend, cần gom P2 sang cuối hoặc bỏ để kịp mốc.

## 18. Kiểm thử và tiêu chí nghiệm thu

- **Bảo toàn số dư:** property test. Sau mọi chuỗi thao tác ngẫu nhiên, `free + locked` = tổng ledger theo từng (wallet, asset), và không bao giờ âm.
- **Công thức:** golden test theo ví dụ trong tài liệu Binance (liq price isolated/cross, one-way/hedge, break-even, funding). Fixture đặt ở `tools/golden` giống cách đang làm với indicator.
- **Khớp lệnh:** bảng test cho từng loại lệnh × TIF × chiều, kèm trường hợp biên: giá đúng bằng limit, gap, trade xảy ra trước thời điểm đặt lệnh (D-77), OCO có hai chân cùng thỏa trong một tick.
- **Replay giống live:** cùng một chuỗi nến 1m cho ra cùng kết quả fill, đúng như test deterministic hiện có.
- **Đồng thời:** hủy và khớp cùng lúc thì chỉ một bên thắng. Hai lệnh đặt cùng lúc dùng chung số dư thì một lệnh bị từ chối.
- **Tích hợp:** Testcontainers (Postgres/Timescale, Redis), giả lập stream Binance bằng fake server.
- **Không ảnh hưởng plan:** toàn bộ test hiện có của trading plan và matching theo plan vẫn pass, không sửa.
- **Coverage:** giữ gate hiện tại của CI. Mỗi BR mới phải có unit test, theo đúng checklist trong PR template.
- **Nghiệm thu UI:** kịch bản demo. Spot mua Limit, OCO chốt lời. Futures Long 20x, thêm margin, TP khớp. Short Cross bị thanh lý. Funding trừ đúng. PnL analysis khớp với ledger.

## 19. Rủi ro và giới hạn của mô phỏng

| Rủi ro / giới hạn | Ảnh hưởng | Cách xử lý |
|---|---|---|
| Lệnh demo không tác động lên thị trường | Lệnh lớn được khớp "đẹp" hơn thực tế | VWAP theo depth (Q-T7). Hiện cảnh báo khi lệnh vượt quá depth. |
| Không biết vị trí trong hàng đợi | Limit có thể khớp sớm hơn thực tế | Chế độ CROSS mặc định (Q-T8) |
| Giới hạn stream Binance (số stream mỗi kết nối, số kết nối) | Không subscribe hết depth và aggTrade cho mọi cặp | Subscribe theo nhu cầu, dùng shard có sẵn, giới hạn danh sách cặp demo |
| Mất stream hoặc server restart | Bỏ lỡ trigger hoặc fill | Replay nến 1m từ watermark (đã có). Fill từ replay gắn `source = REPLAY`. |
| Phạm vi lớn so với nhân lực | Trễ mốc | Làm P0 trước. Cross margin và Hedge có thể dời nếu thiếu thời gian (đã tách giai đoạn). |
| Hiểu nhầm là sàn thật | Rủi ro pháp lý và uy tín | Banner "Demo" trên mọi màn, không có nạp/rút, điều khoản rõ ràng |

Plan dựa trên code ở nhánh

develop

(commit 06c0423) và hành vi công khai của Binance Spot / USDⓈ-M Futures. Các tỉ lệ phí, MMR và giới hạn trong tài liệu chỉ là giá trị mặc định có thể cấu hình. Cần đối chiếu lại với tài liệu Binance hiện hành khi cài đặt.

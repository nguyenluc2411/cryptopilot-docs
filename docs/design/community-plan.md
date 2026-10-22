*Plan · Module community · bản nháp để review*

# CryptoPilot Community Forum: bài viết, comment, like/save, report, media Cloudinary, moderation

Kế hoạch cho phần forum của Trader (SCR-24…27) và phần kiểm duyệt của Admin (SCR-36, đăng thông báo chính thức). Media của bài (ảnh, video) lưu trên **Cloudinary**; backend chỉ lưu `public_id`, URL và metadata.

- **Ngày:** 20/10/2026
- **Nhánh gốc:** `develop` @ `c672c2b`
- **Nhánh đầu tiên:** `feat/t-060-community-posts` (đã tạo)
- **Nguồn yêu cầu:** SRS v1.0 mục 3.7, 3.11.3; UC-26…33, UC-43, UC-44; BR-43…47, BR-57, BR-61, BR-62; CR-04, CR-06; MSG29, MSG32, MSG33, MSG34; D-14, D-58
- **Task:** T-060, T-061, T-063, T-064, T-062, T-084

## 1. Hiện trạng

| Thành phần | Có sẵn | Thiếu |
|---|---|---|
| Schema | V1 có đủ `forum_post`, `post_coin`, `forum_comment`, `engagement`, `post_media`, `post_report` với các CHECK, unique like/save (BR-45), unique report (BR-46) | Không cần bảng mới. Có thể thêm index cho tab Most Liked và bài official |
| Security | `/posts/**`, `/comments/**`, `/media/**` cho TRADER; `/admin/**` cho ADMIN | — |
| Gói | `Feature.VIDEO_POST` (PRO và PREMIUM từ CF-01d) trong `EntitlementApi` | — |
| Setting | `MAX_IMAGES_PER_POST` 4, `MAX_IMAGE_SIZE_MB` 5, `MAX_VIDEO_SIZE_MB` 100, `MAX_VIDEO_DURATION_SECONDS` 300 | `SystemSettingApi` chỉ đọc được `decimal(key)` → thêm `integer(key)` |
| User | `user_profile.display_name`, `avatar_url` | `UserApi` chưa có hàm lấy tên và avatar tác giả theo lô |
| Coin | `MarketApi.coinsBySymbol` | Chưa có hàm kiểm tra coin đang được dùng trong cặp đã listed |
| Outbox | Modulith JDBC registry + `OutboxProcessorJob` (PR #58) | Dùng để xoá media trên Cloudinary sau khi xoá bài, có retry |
| Notification | Bảng `notification` (type gồm `MODERATION`), mail | Chưa có service tạo thông báo in-app. Type chưa có loại cho comment |
| Cloudinary | Biến `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` trong `.env.example` | Chưa có adapter. SDK Cloudinary không có trong TD 1.3 → gọi REST bằng `RestClient`, không thêm dependency |

## 2. Quyết định đề xuất (cần team xác nhận)

| ID | Vấn đề | Đề xuất |
|---|---|---|
| C-01 | Coin tag "enabled coins" (SRS 3.7.2) | Coin hợp lệ khi là base hoặc quote của một cặp đang listed ở ít nhất một market. 0–5 coin, không trùng |
| C-02 | Tab Most Liked "last 7 days" | Bài PUBLISHED tạo trong 7 ngày gần nhất, sắp theo số like giảm dần, hoà thì bài mới hơn trước |
| C-03 | Reply nhiều cấp | Chỉ thụt 1 cấp: trả lời một reply thì lưu `parent_comment_id` = comment gốc |
| C-04 | Thông báo comment mới, kết quả kiểm duyệt | Forum chỉ publish event (`PostCommented`, `PostModerated`). Task notification in-app viết listener, và thêm type mới cho comment bằng migration riêng |
| C-05 | Report trùng | 409, MSG34 (bản "already reported") theo SRS v1.0. Không dùng MSG50 của bản SRS cũ |
| C-06 | Admin đăng bài official | Endpoint riêng `/admin/announcements` (Admin không có role TRADER nên không gọi được `/posts`). Bài official được ghim |
| C-07 | Cách upload media | **Đã chốt (user, 20/10/2026):** cách 4, áp dụng cho cả ảnh và video. Backend ký, trình duyệt upload thẳng lên Cloudinary, backend kiểm tra lại file thật trên Cloudinary trước khi gắn vào bài. Đã loại các cách: chỉ FE (lộ secret hoặc dùng unsigned preset) và upload qua backend (tốn băng thông khi gửi video 100MB) |
| C-08 | Title | Kiểm tra 5–150 ký tự ở tầng app (cột là varchar(255)) |
| C-09 | BAN_USER khi kiểm duyệt | Cần `UserApi.ban(...)`. Nếu T-083 chưa xong thì T-084 thêm hàm này vào `user` |

## 3. Luồng media với Cloudinary

```
FE                         Backend                              Cloudinary
 │ POST /media/upload-signature {mediaType}                         │
 │ ───────────────────────▶ kiểm tra VIDEO_POST (video)             │
 │                          tạo public_id cryptopilot/posts/{userId}/{uuid}
 │                          ký SHA-1(params + api_secret)           │
 │ ◀─── {uploadUrl, apiKey, timestamp, signature, publicId, folder, allowedFormats, maxBytes}
 │ POST uploadUrl (multipart, file + params đã ký) ───────────────▶ │
 │ ◀────────────────────────────────────────────── {public_id, secure_url, bytes, format, duration}
 │ POST /posts {…, media:[{publicId, mediaType}]}                   │
 │ ───────────────────────▶ public_id phải thuộc thư mục của caller │
 │                          GET Admin API resources/{type}/upload/{public_id} ─▶
 │                          ◀── bytes, format, width, height, duration
 │                          kiểm tra BR-44 → sai: MSG32 và xoá file │
 │                          lưu post_media READY, URL lấy từ Cloudinary (không tin URL FE gửi)
 │ ◀─── 201 + MSG33                                                 │
```

- **Chữ ký:** chỉ ký các tham số `folder`, `public_id`, `timestamp`, `allowed_formats`. Chữ ký hết hạn sau 1 giờ (Cloudinary tự kiểm tra `timestamp`).
- **Định dạng:** ảnh JPG/PNG/WEBP, video MP4/WEBM. Video có thumbnail do Cloudinary sinh (URL `.jpg` của video), lưu ở `thumbnail_url`.
- **Một bài:** 1–4 ảnh hoặc đúng 1 video, không trộn (BR-44). Có video thì `post_type` = VIDEO.
- **Xoá bài:** soft delete ngay, publish `PostMediaReleased(publicIds)`. Listener của outbox gọi `destroy` trên Cloudinary, lỗi thì retry. Sửa bài mà bỏ media nào thì cũng xoá theo cách này. Ngoại lệ (A-47): bài HIDDEN, hoặc có báo cáo OPEN/REVIEWING hay đã xử lý HIDE_POST/REMOVE_POST/BAN_USER thì xoá bài không xoá media, job dọn file cũng giữ lại; bài HIDDEN không sửa được.
- **File mồ côi** (đã upload nhưng không gắn vào bài nào): P2. Job hằng ngày liệt kê file trong `cryptopilot/posts/` cũ hơn 24h mà không có trong `post_media`, rồi xoá.
- **Adapter** `community.client.CloudinaryClient`: interface `MediaStorage` gồm `sign`, `describe`, `destroy`. Bản thật chạy trên `RestClient` có timeout; khi thiếu `CLOUDINARY_*` thì profile dev dùng bản giả, còn prod không khởi động (giống cách làm của mail). Test dùng stand-in `com.sun.net.httpserver` theo D-36.
- **Config** `cryptopilot.media.cloudinary.*` (`@ConfigurationProperties`): cloud name, key, secret, base URL, timeout, folder gốc.

## 4. API

Base `/api/v1`, phân trang `{items, page, pageSize, total}` 20/trang (CR-04), thời gian ISO UTC.

### Trader (T-060, T-063, T-064, T-061, T-062)

| Method | Path | Mô tả | Lỗi |
|---|---|---|---|
| GET | `/posts?tab=LATEST\|MOST_LIKED\|SAVED\|MINE&coin=BTC&market=SPOT&page&pageSize` | Feed. MINE có cả bài HIDDEN của mình (kèm status) | 400 MSG15 |
| GET | `/posts/pinned` | Bài official PUBLISHED, mới nhất trước (BR-61) | — |
| GET | `/posts/{id}` | Chi tiết. HIDDEN chỉ tác giả xem được, DELETED thì 404 | 404 MSG41 |
| POST | `/posts` | `{title, content, marketType?, coins[], media[{publicId, mediaType}]}` → 201 | 400 MSG01/MSG15, 400 MSG32, 403 MSG29 |
| PUT | `/posts/{id}` | Sửa bài của mình, cùng body | 404 MSG41 nếu không phải của mình |
| DELETE | `/posts/{id}` | Soft delete (BR-47) → 204 | 404 |
| POST / DELETE | `/posts/{id}/like`, `/posts/{id}/save` | Bật / tắt (BR-45, idempotent) → `{active, count}` | 404 |
| GET | `/posts/{id}/comments?page&pageSize` | Comment gốc cũ trước, mỗi comment kèm danh sách reply | 404 |
| POST | `/posts/{id}/comments` | `{content, parentCommentId?}` 1–2.000 ký tự → 201 | 400, 404 |
| PUT / DELETE | `/comments/{id}` | Sửa / xoá comment của mình. Comment đã xoá mà còn reply thì vẫn trả về với `deleted: true`, không có content | 404 |
| POST / DELETE | `/comments/{id}/like` | BR-45 | 404 |
| POST | `/posts/{id}/reports` | `{reason, description?}` → 201 + MSG34 | 400 OTHER thiếu mô tả, 409 MSG34 report trùng, 409 report bài của mình |
| POST | `/media/upload-signature` | `{mediaType}` → thông số upload ký sẵn | 403 MSG29 với video khi gói không có `VIDEO_POST` (FREE) |

**Một dòng trong feed** gồm:
- `id`, `author {userId, displayName, avatarUrl}`, `title`, `excerpt` (300 ký tự)
- `postType`, `marketType`, `official`, `status`, `coins [symbol]`, `cover` (media đầu tiên)
- `likeCount`, `commentCount`, `likedByMe`, `savedByMe`, `createdAt`, `updatedAt`

**Chi tiết bài** có thêm `content` đầy đủ và `media[]` gồm `mediaType`, `url`, `thumbnailUrl`, `width`, `height`, `durationSeconds`.

### Admin (T-084, UC-43, UC-44)

| Method | Path | Mô tả |
|---|---|---|
| POST / PUT / DELETE | `/admin/announcements[/{id}]` | Bài official; media đi theo luồng mục 3 (`/admin/media/upload-signature`) |
| GET | `/admin/reports-queue?page` | Các bài có report OPEN/REVIEWING, gom theo bài: số report, các lý do, nội dung xem trước |
| GET | `/admin/reports-queue/{postId}` | Chi tiết; mở ra thì chuyển các report sang REVIEWING |
| POST | `/admin/reports-queue/{postId}/decision` | `{action: HIDE_POST\|DISMISS\|WARN_USER\|BAN_USER, note}`; giải quyết mọi report của bài cùng lúc, ghi audit (BR-57), publish `PostModerated` |
| POST | `/admin/posts/{id}/restore` | Hiện lại bài HIDDEN, ghi audit |

### ErrorCode mới

| Code | HTTP | MSG |
|---|---|---|
| `MEDIA_INVALID` | 400 | MSG32 |
| `POST_ALREADY_REPORTED` | 409 | MSG34 |
| `POST_REPORT_OWN_POST` | 409 | MSG43 |
| `MEDIA_NOT_OWNED` | 400 | MSG32 |

## 5. Cấu trúc package `community`

```
community/
  CommunityApi.java                 (nếu module khác cần đếm bài cho SCR-35)
  event/      PostCommented, PostModerated, PostMediaReleased   (@NamedInterface "events")
  controller/ PostController, CommentController, MediaController, AnnouncementController, ModerationController
  service/    PostService, CommentService, EngagementService, ReportService, MediaService, ModerationService
  service/impl/ …Impl, PostAssembler (map entity → response), MediaRules (BR-44)
  repository/ ForumPostRepository, PostCoinRepository, ForumCommentRepository, EngagementRepository,
              PostMediaRepository, PostReportRepository
  entity/     ForumPost, PostCoin, ForumComment, Engagement, PostMedia, PostReport
  model/enums/ PostType, PostStatus, CommentStatus, EngagementAction, MediaType, MediaStatus,
              ReportReason, ReportStatus, ResolutionAction, FeedTab   (+ package-info @NamedInterface "enums")
  model/      MediaDescriptor, UploadSignature, FeedQuery
  dto/request, dto/response
  client/     MediaStorage, CloudinaryClient, LoggingMediaStorage (dev), CloudinaryProperties
  job/        MediaReleaseListener (@ApplicationModuleListener), OrphanMediaSweepJob (P2)
```

Theo D-48: interface để trong `service/`, implementation để trong `service/impl/`. DTO không phụ thuộc entity. Enum để trong `model/enums`. Không ghi vào bảng của module khác.

**Thay đổi ở module khác:**
- `user`: `UserApi.profiles(Collection<UUID>) → List<AuthorCard>`. T-084 thêm `ban(...)` nếu T-083 chưa có.
- `market`: `MarketApi.listedCoinsBySymbol(...)`.
- `admin`: `SystemSettingApi.integer(key)`.

## 6. Các giai đoạn và nhánh

Mỗi task làm trên một nhánh riêng tách từ `develop` mới nhất (pull trước). Nếu task trước chưa merge thì tách nhánh từ nhánh của task trước và retarget PR sau khi task trước merge, như đã làm với #47/#48. **Migration:** V26 đã dùng ở `feat/t-044-exit-rules` (chưa merge), nên migration của community bắt đầu từ **V27**; trước khi merge phải kiểm tra lại số.

| # | Task | Nhánh | Nội dung | Phụ thuộc |
|---|---|---|---|---|
| 1 | **T-060** Bài viết | `feat/t-060-community-posts` | Entity, enum, repository; CRUD bài text; coin tag (C-01); soft delete; feed 4 tab + filter + `/posts/pinned`; đếm like/comment theo lô; tên/avatar tác giả; HIDDEN/DELETED theo BR-47; announcement của Admin (C-06) | — |
| 2 | **T-061** Media Cloudinary | `feat/t-061-cloudinary-media` | `MediaStorage` + `CloudinaryClient` (sign, describe, destroy), properties, bản giả cho dev; `/media/upload-signature`; gắn media khi tạo/sửa bài, kiểm tra BR-44 server-side; xoá qua outbox; `.env.example` | T-060 |
| 3 | **T-062** Video PREMIUM | cùng nhánh T-061 hoặc `feat/t-062-video-post` | `VIDEO_POST` ở bước cấp chữ ký và tạo bài → MSG29; video cũ vẫn xem được khi hết gói (BR-43) | T-061 |
| 4 | **T-063** Comment, like, save | `feat/t-063-comments-engagement` | Comment/reply 1 cấp (C-03), sửa/xoá, hiển thị "Comment deleted"; like bài/comment, save bài (BR-45, test constraint); tab Saved; event `PostCommented` | T-060 |
| 5 | **T-064** Report | `feat/t-064-post-reports` | Report BR-46, MSG34, OTHER bắt buộc mô tả | T-060 |
| 6 | **T-084** Kiểm duyệt | `feat/t-084-moderation` | Hàng đợi gom theo bài, REVIEWING khi mở, 4 quyết định, restore, audit, `PostModerated` | T-064, T-081 (xong) |
Phần FE (T-065, SCR-36 của T-087) có plan riêng trong repo FE, không ghi ở đây.

Ước tính: T-060 khoảng 2 ngày, T-061 + T-062 khoảng 2 ngày, T-063 khoảng 1,5 ngày, T-064 khoảng 0,5 ngày, T-084 khoảng 1,5 ngày.

## 7. Test (Definition of Done)

- Tên test theo dạng `<RuleId>_<Scenario>_<Expected>`, ví dụ `BR47_aHiddenPost_isInvisibleToOthers_butVisibleToItsAuthor`.
- **API test** (Testcontainers, theo mẫu `WatchlistApiTest`) cho mỗi endpoint:
  - quyền: Guest 401, Admin không gọi được `/posts`, Trader không gọi được `/admin`;
  - quyền sở hữu: bài của người khác trả 404;
  - phân trang, đủ 4 tab, filter coin/market, bài ghim.
- **Constraint test:**
  - like/save trùng (BR-45), kể cả hai request cùng lúc;
  - report trùng và report bài của mình (BR-46).
- **Media:**
  - stand-in Cloudinary: chữ ký đúng thuật toán (so với ví dụ trong tài liệu Cloudinary);
  - file quá dung lượng, sai định dạng, video quá 5 phút, `public_id` của người khác → MSG32;
  - xoá bài → `destroy` được gọi qua outbox, lỗi thì retry.
- **Gói:** FREE xin chữ ký video hoặc tạo bài video → MSG29 (PRO được đăng video từ CF-01d); hết gói → video cũ vẫn hiển thị.
- **Kiểm duyệt:** mọi report của bài được giải quyết cùng lúc; có audit; quyết định lỗi thì không có dòng audit nào.
- Chạy `./mvnw clean verify` sau mỗi lần checkout. `ModularityTest` và `PackageConventionTest` phải pass. Cập nhật OpenAPI, TECHNICAL_DESIGN 8 và fe-guide `modules/community.md` khi API đã chốt.

## 8. Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Lộ `api_secret` Cloudinary | Secret chỉ nằm ở backend (env), FE chỉ nhận chữ ký. Không log chữ ký và secret |
| FE gửi URL giả hoặc file của người khác | Backend không nhận URL từ FE, chỉ nhận `public_id` trong thư mục của caller, rồi đọc metadata thật từ Cloudinary |
| Cloudinary chậm hoặc lỗi lúc tạo bài | Timeout và báo lỗi rõ ràng; xoá file chạy qua outbox có retry |
| Feed chậm vì đếm like/comment | Đếm theo lô bằng một query `GROUP BY` cho các bài trong trang; có index `engagement(post_id)`, `forum_comment(post_id)` |
| Trùng số migration với nhánh khác | Bắt đầu từ V27, kiểm tra trước khi merge |

## 9. Lưu ý: tính năng có thể làm thêm (ngoài SRS, chưa duyệt)

Ghi lại ngày 20/10/2026, sau khi xong backend T-060…T-064 và T-084. Forum hiện có phần lõi giống CoinMarketCap Community, nhưng thiếu nhiều tính năng "mạng xã hội". Các mục dưới đây **không có trong SRS v1.0**. Muốn làm thì phải được team/giảng viên duyệt, cập nhật SRS và logical model trước, sau đó mới mở task (xem A-43 trong `CURRENT_STATE.md`, mục 5).

### 9.1 So sánh với CoinMarketCap Community

So với hiểu biết chung về CMC Community, có thể chưa khớp hoàn toàn với phiên bản mới nhất của họ.

| Tính năng | CMC Community | CryptoPilot (SRS v1.0) |
|---|---|---|
| Feed bài viết, tab Latest/Top | Có | ✅ Có (Latest, Most Liked 7 ngày, Saved, My Posts) |
| Gắn coin vào bài, lọc theo coin | Có (kiểu `$BTC`) | ✅ Có (0–5 coin, lọc theo coin và market) |
| Ảnh, video | Có | ✅ Có (4 ảnh hoặc 1 video; video cho PRO và PREMIUM) |
| Like, comment, reply | Có | ✅ Có |
| Lưu bài (bookmark) | Có | ✅ Có |
| Report vi phạm, Admin kiểm duyệt | Có | ✅ Có |
| Bài official được ghim | Có (bài của dự án/CMC) | ✅ Có (announcement của Admin) |
| Bình chọn Bullish/Bearish cho bài hoặc coin | Có | ❌ Không có trong SRS |
| Follow người dùng, feed "Following" | Có | ❌ Không có |
| Trang cá nhân (profile, bài đã đăng, follower) | Có | ❌ Chỉ có tab My Posts của chính mình |
| Tìm kiếm bài, hashtag, chủ đề trending | Có | ❌ Không có |
| Repost/share, poll | Có | ❌ Không có |
| Hiện giá coin ngay trong bài | Có | ❌ Chưa, dù backend đã có sẵn dữ liệu giá |
| Thông báo khi có người comment, like hoặc bị kiểm duyệt | Có | ⚠️ Backend đã phát event `PostCommented` và `PostModerated`, chưa tạo thông báo in-app |

### 9.2 Đề xuất theo thứ tự nên làm

| # | Tính năng | Backend cần gì | Công | Ghi chú |
|---|---|---|---|---|
| E-1 | Thông báo in-app khi có comment mới hoặc bài bị kiểm duyệt | Listener cho `PostCommented` và `PostModerated` ghi vào `notification`; thêm type cho comment (migration mới, CHECK hiện chỉ có `ALERT`, `PLAN`, `MODERATION`, `SUBSCRIPTION`); bỏ qua comment của chính tác giả | Nhỏ | **Đã có trong SRS** (3.7.3, 3.11.3), chỉ chưa làm: đi cùng task notification in-app, không cần duyệt thêm |
| E-2 | Tag Bullish/Bearish khi đăng bài, tỷ lệ bullish/bearish theo coin | Cột `sentiment` (BULLISH, BEARISH hoặc null) trên `forum_post`; filter feed theo sentiment; endpoint tổng hợp theo coin trong 24h/7 ngày | Nhỏ | Hợp với app trading; nhớ disclaimer MSG42 (BR-60) vì gần với tín hiệu mua bán |
| E-3 | Giá và % thay đổi 24h của coin được gắn trên thẻ bài | Không cần API mới: FE đọc `GET /market/...` hoặc STOMP ticker theo symbol | Rất nhỏ (FE) | Lưu ý giới hạn số subscription STOMP khi feed có nhiều coin |
| E-4 | Trang profile công khai của trader | `GET /users/{id}/profile` (tên, avatar, số bài) và `GET /posts?author={id}` | Nhỏ | Không lộ email, không lộ dữ liệu trading cá nhân |
| E-5 | Tìm kiếm bài theo từ khoá | `GET /posts?q=`: bắt đầu bằng `ILIKE` trên title; sau đó dùng Postgres full-text (`tsvector` + GIN index) | Vừa | Tiếng Việt không có dictionary sẵn của Postgres; dùng `simple` hoặc `unaccent` |
| E-6 | Follow người dùng, tab Following | Bảng mới `user_follow (follower_id, followee_id)`, unique, không tự follow; tab feed mới | Vừa | Thêm thông báo khi người mình follow đăng bài |
| E-7 | Hashtag và chủ đề trending | Bảng `post_tag`, tách hashtag khi đăng; trending = đếm theo cửa sổ thời gian | Vừa | Coin tag hiện có đã che một phần nhu cầu này |
| E-8 | Repost/share, poll | Bảng mới cho repost và cho poll/vote | Lớn | Ưu tiên thấp so với mục tiêu chính của đồ án |

### 9.3 Việc kỹ thuật còn treo (trong phạm vi hiện tại)

- ~~**Dọn file Cloudinary mồ côi**~~ **Xong 21/10 (`cf-06`, `5255425`):** `MediaSweepJob` chạy 00:45 UTC hằng ngày (bật ở dev/prod), liệt kê `cryptopilot/posts/` cũ nhất trước, xoá file cũ hơn 24h mà không bài nào (trừ bài DELETED) còn mang; tối đa 20 trang × 500 file mỗi loại mỗi lần chạy (`cryptopilot.media.sweep.*`).
- **Giới hạn số request mỗi giờ của Cloudinary Admin API:** mỗi file mới tốn 1 request để kiểm tra. Đủ cho demo; nếu dùng thật thì cân nhắc nâng gói, hoặc thêm giới hạn số chữ ký upload cho mỗi user.
- **FE:** T-065 (feed, chi tiết bài, form đăng bài có upload Cloudinary, dialog report) và SCR-36 của T-087 (hàng đợi kiểm duyệt). Plan FE viết trong repo FE.

## 10. Quyết định 20/10/2026: theo file đăng ký đề tài, phần còn lại làm giống CoinMarketCap (D-99)

Người dùng chốt: forum **làm theo file đăng ký đề tài** (`CryptoPilot_Capstone_Project_Full_Formatted.docx`) ở những chỗ nó khác SRS v1.0. Những gì file đăng ký không nhắc tới thì **làm giống CoinMarketCap Community**. SRS và logical model phải được cập nhật theo (A-44); các mục E-x ở mục 9 vì vậy không còn chỉ là ý tưởng.

### 10.1 Giai đoạn 1: khớp file đăng ký (nhánh `feat/cf-01-registration-alignment`)

| # | File đăng ký | Thay đổi | SRS v1.0 trước đó |
|---|---|---|---|
| CF-01a | Guest: "View public forum posts and coin-related discussions" | Guest **đọc** được feed LATEST/MOST_LIKED, bài ghim, chi tiết bài, comment; tab SAVED/MINE và mọi thao tác ghi vẫn cần Trader | Forum chỉ cho Trader |
| CF-01b | "coin-related discussions" trên Coin Detail | `GET /posts/coins/{symbol}/summary` (số bài 24h/7 ngày, bài mới nhất), dùng chung với `?coin=`; công khai | Không có |
| CF-01c | Admin: "hide **or remove** inappropriate content" | Quyết định mới `REMOVE_POST` (bài thành DELETED, audit `POST_REMOVED`); migration mở rộng CHECK `resolution_action` | Chỉ HIDE_POST, DISMISS, WARN_USER, BAN_USER |
| CF-01d | Video cho "Traders with an active package" | Migration: `can_post_video = true` cho gói PRO (giá trị cấu hình theo tier, D-58) | Chỉ PREMIUM |
| CF-01e | Admin: "official posts, announcements, and educational content (e.g. platform updates, market education)" | Bài official có `official_category`: ANNOUNCEMENT, PLATFORM_UPDATE, EDUCATION; lọc bài ghim theo loại | Một loại bài official |

Ngoài forum, file đăng ký còn yêu cầu thống kê "forum activity" (T-086), quản lý trạng thái tài khoản (T-083) và web cho Guest (T-065). Các mục này làm trong task của chúng.

### 10.2 Giai đoạn 2: giống CoinMarketCap Community

> **Đã thu hẹp ngày 21/10/2026 (mục 12):** chỉ giữ E-4 (profile công khai) và E-5 (tìm kiếm). E-2, E-3, E-6, E-7, E-8 ngoài phạm vi.

Thứ tự đề xuất (chi tiết backend ở mục 9.2): E-2 Bullish/Bearish → E-4 trang profile công khai → E-5 tìm kiếm → E-6 follow và tab Following → E-7 hashtag và trending → E-8 repost và poll. E-3 (giá coin trên thẻ bài) là việc của FE. E-1 (thông báo in-app) có sẵn trong SRS, làm cùng task notification.

Mỗi mục làm trên một nhánh riêng `feat/cf-0x-...`, nối tiếp nhánh trước. Migration của forum bắt đầu từ V27; kiểm tra lại số trước khi merge, vì V26 đang ở `feat/t-044-exit-rules`.

### 10.3 Tiến độ (20/10/2026)

| Nhánh | Nội dung | Commit |
|---|---|---|
| `feat/cf-01-registration-alignment` | Giai đoạn 1: Guest đọc forum, thảo luận theo coin, REMOVE_POST, video cho PRO, loại bài official | `d2f8a25`, `1f7f836` |
| `feat/cf-02-sentiment` | E-2 Bullish/Bearish trên bài, bình chọn hằng ngày theo coin | `7bd736f` |
| `feat/cf-03-profiles-follow` | E-4 trang profile công khai, E-6 follow và tab Following | `632eceb` |
| `feat/cf-04-search-trending` | E-5 tìm kiếm, E-7 hashtag và trending | `3ebf9ed` |

Còn lại: E-8 repost và poll; E-1 thông báo in-app (làm cùng task notification); E-3 giá coin trên thẻ bài (FE).

## 11. Dừng ở đây (20/10/2026), mai làm tiếp

### 11.1 Trạng thái các nhánh backend (repo `cryptopilot_project`, chỉ commit local, CHƯA push)

Các nhánh nối tiếp nhau, nhánh sau tách từ nhánh trước. Khi mở PR thì merge theo đúng thứ tự này và retarget PR sau khi PR trước merge.

| # | Nhánh | Task | Commit | Test toàn bộ |
|---|---|---|---|---|
| 1 | `feat/t-060-community-posts` | T-060 bài viết, feed, bài ghim | `c6c88e7`, `ea64cc8` | 2986/2986 ✅ |
| 2 | `feat/t-061-cloudinary-media` | T-061 Cloudinary, T-062 video | `412d890`, `6843e19`, `5c02181` | 3022/3022 ✅ |
| 3 | `feat/t-063-comments-engagement` | T-063 comment, like, save | `5983183` | (gộp vào #4) |
| 4 | `feat/t-064-post-reports` | T-064 report | `b68ed20` | 3058/3058 ✅ |
| 5 | `feat/t-084-moderation` | T-084 kiểm duyệt, ban | `a4e6fe2`, `65e12cb` | 3071/3071 ✅ |
| 6 | `feat/cf-01-registration-alignment` | D-99 giai đoạn 1 (file đăng ký) | `d2f8a25`, `1f7f836` | 3083/3083 ✅ |
| 7 | `feat/cf-02-sentiment` | E-2 Bullish/Bearish | `7bd736f` | (gộp vào #8) |
| 8 | `feat/cf-03-profiles-follow` | E-4 profile, E-6 follow | `632eceb` | 3100/3100 ✅ |
| 9 | `feat/cf-04-search-trending` | E-5 tìm kiếm, E-7 hashtag/trending | `3ebf9ed`, `79e12bc` | (xem #10) |
| 10 | `feat/cf-05-notifications` | E-1 thông báo in-app (21/10) | `163ad18` | 3115/3116, lỗi còn lại (DTO phụ thuộc entity) đã sửa trong commit; test kiến trúc + `NotificationApiTest` chạy lại đạt |
| 11 | `feat/cf-06-predeploy-hardening` | Dọn file Cloudinary mồ côi; giới hạn tần suất cho Guest (rule `guest` 300/phút/IP, ADR-014 amendment) | `5255425`, `09c9ac8` | xem B2 |

Repo đang đứng ở nhánh `feat/cf-05-notifications`. Migration của forum: V27 → V32 (V26 thuộc `feat/t-044-exit-rules`, đã merge vào `develop` ngày 21/10). Test flaky có từ trước, không liên quan forum: `AlertEngineTest.NSF06_aCommittedEdit_replacesTheRuleInTheBook`.

### 11.2 Những gì đã sửa ngoài module `community`

- `user`: `UserApi.authors`, `UserApi.banForModeration` (+ event `AccountSuspended`), `UserApi.publicProfile`; `AuthorCard`, `PublicProfile`.
- `auth`: `SuspendedAccountSessions` thu hồi mọi session khi bị ban; `SecurityConfig` thêm `PUBLIC_COMMUNITY` (Guest đọc) và `/api/v1/community/**` vào vùng Trader.
- `market`: `MarketApi.listedCoinsBySymbol`.
- `admin`: `SystemSettingApi.integer`; `AuditAction` thêm `USER_WARNED`, `POST_REMOVED`.
- `billing`: V28 cho gói PRO quyền `VIDEO_POST` (D-99); đã sửa test Table 3.1 theo.
- `common`: `ErrorCode` thêm `MEDIA_INVALID`, `MEDIA_STORAGE_UNAVAILABLE`, `POST_ALREADY_REPORTED`, `POST_REPORT_OWN_POST`, `POST_NOT_HIDDEN`, `FOLLOW_SELF`.
- Cấu hình: `cryptopilot.media.cloudinary.*` trong `application.yml`, nhóm Media storage trong `deploy/.env.example`.
- Test hạ tầng đã cập nhật: `OpenApiDocsTest` (danh sách path), `AuthorizationMatrixTest`, `BaselineSchemaTest` (53 bảng), `SchemaCatalogueTest`, `expected-columns.csv`, `expected-enums.csv`, `EnumCheckConstraintTest` (mẫu cho kiểu `date`).

### 11.3 Việc tiếp theo (chọn khi làm tiếp)

1. ~~**E-1 thông báo in-app:**~~ **Xong 21/10 (nhánh #10, migration V32).** Chưa làm: thông báo ALERT từ `AlertTriggered` và gửi email/push (thuộc T-056/T-058, báo người phụ trách). Nội dung tự viết bằng tiếng Anh, chưa có mã MSG trong SRS. listener cho `PostCommented`, `PostModerated`, `UserFollowed` ghi vào `notification` (cần migration thêm type cho comment và follow), và API đọc/đánh dấu đã đọc. Đây cũng là phần còn thiếu của SRS 3.7.3 và 3.11.3.
2. **E-8 repost và poll** (lớn, ưu tiên thấp).
3. **FE T-065:** feed (có ô tìm kiếm), chi tiết bài, form đăng bài có upload Cloudinary (form ký trước, rồi upload thẳng), dialog report, khối thảo luận trên trang coin, trang profile công khai, trung tâm thông báo. Làm trong repo FE: pull `develop`, tạo nhánh riêng, viết plan FE trong repo FE.
4. **Trước khi deploy:** ~~job dọn file Cloudinary mồ côi~~ và ~~rate limit cho Guest~~ xong ở `cf-06` (21/10). ~~Thử upload thật với key Cloudinary~~ **xong 21/10** trên nhánh `cf-07`: ký form, upload ảnh thẳng lên Cloudinary, đăng bài (backend đọc lại file thật), Guest thấy ảnh bìa trên feed, `publicId` không tồn tại bị từ chối 400, xoá bài thì file bị xoá khỏi Cloudinary. Còn (tuỳ chọn): giới hạn chữ ký upload theo user.
5. **Docs:** ✅ (22/10/2026, A-44 và A-47) sửa SRS theo A-44 (Guest đọc forum, REMOVE_POST, video cho PRO, loại bài official) và E-4, E-5 của D-99 giai đoạn 2; cập nhật fe-guide `modules/community.md` khi bắt đầu FE.
6. **Push và mở PR** cho các nhánh ở 11.1 khi team sẵn sàng review.

## 12. Chốt phạm vi trước khi merge (21/10/2026)

Người dùng chốt: merge vào `develop` là xong, không sửa thêm. Forum chỉ gồm SRS v1.0, file đăng ký (giai đoạn 1, mục 10.1), E-1 thông báo in-app (có trong SRS), **E-4 trang profile công khai** và **E-5 tìm kiếm**.

| Mục | Quyết định |
|---|---|
| E-2 Bullish/Bearish, vote coin theo ngày | Bỏ |
| E-3 giá coin trên thẻ bài | Bỏ |
| E-6 follow, tab Following, thông báo FOLLOW | Bỏ |
| E-7 hashtag, trending | Bỏ |
| E-8 repost, poll | Bỏ (chưa từng làm) |

Gỡ trên nhánh `feat/cf-07-scope-trim` (tách từ `cf-06` đã merge `origin/develop` @ `132c480`, không conflict, 3171/3171 test đạt trước khi gỡ):

- Xoá migration V29 (sentiment), V30 (follow), V31 (hashtag); V32 thông báo đổi số thành **V29** và bỏ type FOLLOW. Vì nhánh chưa merge nên sửa thẳng migration; DB dev đã chạy V27–V32 thì phải xoá và dựng lại (`docker compose down -v`) hoặc `flyway clean`.
- Xoá API `/posts/trending`, `/posts/coins/{symbol}/sentiment`, `/community/members/{id}/follow`, `/followers`, `/following`; bỏ filter `sentiment`, `hashtag`, tab FOLLOWING, trường `sentiment`, `hashtags[]` của bài; bỏ `followers`, `following`, `followedByMe` của profile; bỏ `ErrorCode.FOLLOW_SELF`, `NotificationType.FOLLOW`, `NotificationReference.MEMBER`.
- Giữ `GET /community/members/{id}` và filter `author`, `q` của feed. Test tìm kiếm chuyển sang `SearchApiTest`.


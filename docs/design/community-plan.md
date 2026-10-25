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
| `MEDIA_KEPT_AS_EVIDENCE` | 400 | MSG56 (sửa bài bỏ media đang là bằng chứng kiểm duyệt, A-47) |
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


## 13. Làm thêm sau khi merge (25/10/2026, D-125)

Người dùng mở lại phạm vi để forum đủ như một diễn đàn: lấy lại E-6 (follow), thêm chặn người dùng, report comment, thông báo reply, @mention, lượt xem, và ẩn nội dung của người bị ban. Quy tắc của người dùng: **không tạo thêm bảng riêng**, chỉ một bảng mới cho quan hệ giữa thành viên.

Nhánh `feat/community-forum-extras` (từ `origin/develop` `5f29dc6`), migration **V36** `V36__community_extras.sql`. PCI cũng đang giữ V35 và sẽ phải đổi lên V36: nhánh nào merge sau thì đổi số.

| Tính năng | Lưu ở đâu | API |
|---|---|---|
| Follow (E-6) và chặn | Bảng mới `user_relation (source_user_id, target_user_id, relation_type FOLLOW/BLOCK)`, một dòng mỗi chiều nên follow và chặn loại trừ nhau | `POST/DELETE /community/members/{id}/follow`, `/block`; `GET /community/members/{id}/followers`, `/following` (công khai); `GET /community/blocks` (của mình) |
| Report comment | `post_report` thêm `comment_id` (null = report bài) và `reported_content` (text lúc report); hai partial unique index thay `uq_post_report_post_reporter`; action mới `HIDE_COMMENT`, `REMOVE_COMMENT`, CHECK action khớp loại report | `POST /comments/{id}/reports`; admin `GET /admin/comment-reports-queue`, `GET .../{commentId}`, `POST .../{commentId}/decision`, `POST /admin/comments/{id}/restore` |
| Thông báo reply | Không đổi DB; `PostCommented` thêm `repliedToAuthorId` | type `COMMENT`, "X replied to your comment." |
| @mention | Không lưu; request bài và comment thêm `mentions: [userId]` (tối đa 10); type thông báo mới `MENTION`, khoá nguồn theo bài/comment + người nên sửa bài không báo lại | `GET /community/members?q=` (gợi ý tên, tối đa 10) |
| Lượt xem | `engagement` thêm action `VIEW` (chỉ cho bài), mỗi người đăng nhập khác tác giả tính một lần, khách không tính | `viewCount` trong thẻ và chi tiết bài |
| Ẩn nội dung người bị ban | Không đổi DB; event mới `user.event.AccountBanned` ở cả hai đường ban; `BannedMemberListener` ẩn bài và comment còn PUBLISHED, xoá follow và chặn của họ | — |

Quy tắc nghiệp vụ:

- Không follow hay chặn chính mình (`FOLLOW_SELF`, `BLOCK_SELF`), không follow hay chặn Admin (`RELATION_NOT_ALLOWED`; Admin chỉ đăng bài official mà tab Following bỏ qua, và không đọc được `/notifications`). Bỏ follow hay bỏ chặn người chưa có quan hệ vẫn trả 200.
- Chặn có hiệu lực **hai chiều** (`CommunityAccess`): A chặn B thì cả A lẫn B không thấy bài (mọi tab trừ MINE, kể cả mở link trực tiếp), comment, số comment của nhau; không like, lưu, report, comment hay reply nội dung của nhau. Nội dung bị chặn trả **404 (MSG41)** như không tồn tại, để không lộ việc bị chặn. Follow xoá hai chiều; B follow A trả 404, A follow B trả `RELATION_NOT_ALLOWED` (409, A phải bỏ chặn trước). Mention và gợi ý tên bỏ qua người có quan hệ chặn.
- Trang cá nhân: B mở trang A (người chặn mình) nhận 404, kể cả danh sách follower/following của A; A vẫn mở được trang B (`blockedByMe = true`) để bỏ chặn. Danh sách follower/following của bất kỳ ai cũng bỏ qua những người có quan hệ chặn với người đang xem.
- Comment bị ẩn: tác giả không sửa, không xoá được (giữ nguyên cho kiểm duyệt); nếu là comment đầu thread còn reply thì hiện placeholder `hidden = true`, không có nội dung và tác giả. `REMOVE_COMMENT` chuyển comment sang DELETED.
- Hàng đợi report bài chỉ gồm report có `comment_id` null; quyết định bài từ chối `HIDE_COMMENT`/`REMOVE_COMMENT` (400), quyết định comment từ chối `HIDE_POST`/`REMOVE_POST` (400). Audit mới: `COMMENT_HIDDEN`, `COMMENT_REMOVED`, `COMMENT_RESTORED`, entity `FORUM_COMMENT`.
- Mention bỏ qua id không tồn tại, bị ban, Admin, chính tác giả: không báo lỗi, vì danh sách gợi ý có thể đã cũ.
- Khi ban: nội dung bị ẩn không ghi audit từng dòng (lệnh ban đã có audit). Admin **không** khôi phục được bài hay comment của người đã bị ban (`AUTHOR_BANNED`, 409), vì ban là vĩnh viễn.
- Mỗi bài hoặc comment báo mention cho tối đa 10 người, tính dồn qua mọi lần sửa (đếm theo khoá nguồn trong `notification`, dưới advisory lock theo bài/comment nên hai lần sửa cùng lúc cũng không vượt 10).
- Dashboard admin (T-086): `openReports` chỉ đếm report bài, thêm `openCommentReports` cho report comment.
- Follow và chặn khoá theo từng cặp thành viên (`UserLock`, scope `community-relation`), để follow ngược lại không lọt qua lúc đang bị chặn.
- Số comment của bài (`commentCount`) không tính comment của người có quan hệ chặn với người xem, khớp với danh sách comment.
- Còn lại (chấp nhận): thông báo cũ do người kia tạo trước khi chặn vẫn nằm trong hộp thông báo, bấm vào sẽ ra 404; các con số tổng hợp công khai (số bài, số follower, thảo luận theo coin) vẫn đếm mọi người.

Còn lại cho FE: nút follow/chặn trên trang thành viên, danh sách chặn, dialog report comment, hàng đợi comment trong SCR-36, ô gợi ý @mention, placeholder comment bị ẩn, hiện `viewCount`.

## 14. Giao diện kiểu CoinMarketCap Community (25–26/10/2026, D-99, D-125)

Người dùng yêu cầu FE community giống khoảng 90% trang CoinMarketCap Community (ảnh tham khảo chỉ để trên máy, không commit). Quyết định của người dùng: tiêu đề bài do người viết tự gõ (không tự sinh); bỏ Repost, Poll, GIF và Live. Articles là bài official theo chuyên mục; Topics là coin đang được bàn nhiều.

### 14.1 BE thêm trên `feat/community-forum-extras` (chưa commit)

| Tính năng | Lưu ở đâu | API |
|---|---|---|
| Tác giả gắn nhãn Bullish/Bearish cho bài | `forum_post.sentiment` (null, `BULLISH`, `BEARISH`), CHECK `ck_forum_post_sentiment`; `PostRequest.sentiment` (để trống = không gắn) | trường `sentiment` của bài |
| Người đọc vote Bullish/Bearish | `engagement.action_type` thêm `BULLISH`, `BEARISH` (chỉ cho bài); partial unique index `uq_engagement_post_vote (user_id, post_id)` nên mỗi người một phiếu, vote lại là đổi phiếu (upsert) | `PUT /posts/{id}/vote` `{sentiment}`, `DELETE /posts/{id}/vote`; bài có `bullishCount`, `bearishCount`, `myVote` |
| Tab For You | `FeedTab.TRENDING`, không đổi DB: điểm = (like + vote) × 3 + comment × 4 + view × 0,5 + 1, chia cho (tuổi bài tính bằng giờ + 2) mũ 1,5 (kiểu Hacker News), không gồm bài official | `GET /posts?tab=TRENDING` |
| Coin đang được bàn | Đếm tag coin của bài gần đây | `GET /posts/trending-coins?limit=` (công khai) |
| Điểm tác giả và Top Influencers | Tính bằng SQL, không lưu: ảnh hưởng = 40·ln(1+follower) + 25·ln(1+like) + 15·ln(1+comment) + 10·ln(1+bài); độ sâu = 50·ln(1+bài sâu) + 20·ln(1+like) + 10·ln(1+comment), bài sâu là bài có media hoặc nội dung từ 600 ký tự | `authorStanding` trên mỗi bài; `GET /community/influencers?rank=INFLUENCE|DEPTH&limit=` (công khai) |

Vẫn trong migration `V36__community_extras.sql`, không thêm bảng. Test mới `CommunityRankingApiTest` (5); `OpenApiDocsTest` 131 operation; `clean verify` 4019/4019, đạt ngưỡng coverage (25/10).

**Phải làm trước khi commit:** develop đã có `V36__journal_exits.sql` (T-048b, #75), nên migration này phải đổi sang số còn trống; PCI cũng đang chờ một số mới. Các comment trong code đã đổi D-121 → D-125.

### 14.2 FE (để cả nhóm biết BE nào cần)

- Nhánh FE `feat/community-cmc-ui` (`0bd6c13`) đã merge thẳng vào FE `develop` ngày 25/10 (`20788b5`, không qua PR, theo yêu cầu người dùng).
- Bố cục 3 cột: danh sách coin bên trái (giá, % 24h), feed ở giữa, bên phải là bài ghim, Top Influencers, thảo luận coin đang chọn, nội quy. Feed mặc định **Latest** (bài mới nhất trên cùng), For You / Following / Saved trong menu, 10 bài mỗi trang, phân trang có số (`?page=` trên URL). Dialog Post: ô Title và Content riêng, gõ `$` để chọn coin, Bullish/Bearish, ảnh, emoji. Follow và chặn trên thẻ bài, trang thành viên và menu bài.
- **Chạy FE develop với BE develop:** Latest, đăng bài, comment, like, follow vẫn dùng được; Top Influencers, coin đang được bàn, vote và tab For You lỗi hoặc trống cho tới khi `feat/community-forum-extras` vào develop.
- FE chưa làm phần còn lại của mục 13: dialog report comment, hàng đợi report comment trong SCR-36, gợi ý @mention.

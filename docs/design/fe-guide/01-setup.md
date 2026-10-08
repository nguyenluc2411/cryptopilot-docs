# 01 · Setup

## Base URLs

| Environment | REST base | STOMP endpoint | Status |
|---|---|---|---|
| Local (`dev` profile) | `http://localhost:8080/api/v1` | `ws://localhost:8080/ws` | Works today |
| Staging (VPS, `prod` profile) | not decided | not decided | Q-07 open (host and domain); T-096 |
| Production | — | — | No production environment is planned before the demo |

Put the base URLs in client config, never in code:

| Client | Suggested keys |
|---|---|
| Web (Vite) | `VITE_API_BASE_URL=http://localhost:8080/api/v1`, `VITE_WS_URL=ws://localhost:8080/ws` |
| Mobile (Flutter) | `--dart-define=API_BASE_URL=...`, `--dart-define=WS_URL=...` (Android emulator: host is `10.0.2.2`, not `localhost`) |

`deploy/.env.example` already names `PUBLIC_BASE_URL=http://localhost:5173` (the web origin) and
`API_BASE_URL=http://localhost:8080`. The backend does not read them yet.

## CORS — read this before the first browser call

| Channel | What the code does | Effect for the web app |
|---|---|---|
| REST `/api/v1/**` | `common.config.CorsConfig` (D-83, review R-05): origins from `CORS_ALLOWED_ORIGINS`; methods GET, POST, PUT, PATCH, DELETE, OPTIONS; request headers `Authorization`, `Content-Type`, `Accept`, `X-Correlation-Id`; exposed headers `X-Correlation-Id`, `Retry-After`; no credentials; preflight cached 1 h | A page on an allowed origin calls the API directly. Any other origin is refused with 403 before the API |
| STOMP `/ws` | The same `CORS_ALLOWED_ORIGINS` list | Same origins as REST |

| Profile | `CORS_ALLOWED_ORIGINS` default |
|---|---|
| `dev` | `http://localhost:*,http://127.0.0.1:*` — any local port |
| `prod` (also staging, TD 12) | none: every cross-origin caller is refused until it is set |
| no profile (tests) | none |

With the `dev` profile, `VITE_API_BASE_URL=http://localhost:8080/api/v1` and
`VITE_WS_URL=ws://localhost:8080/ws` work without a proxy. A Vite dev proxy remains an option when the
web app should see one origin (for example to mirror a same-origin deployment):

```ts
// vite.config.ts (web repo)
export default defineConfig({
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8080', changeOrigin: true },
      '/ws': { target: 'ws://localhost:8080', ws: true },
    },
  },
});
```

With the proxy, use `VITE_API_BASE_URL=/api/v1` and `VITE_WS_URL=ws://localhost:5173/ws`. Mobile apps
are not affected by CORS.

Source: `backend/src/main/java/com/cryptopilot/common/config/CorsConfig.java#L34`;
`backend/src/main/java/com/cryptopilot/auth/config/SecurityConfig.java#L223`; `backend/src/main/java/com/cryptopilot/common/config/WebSocketConfig.java#L67`;
`backend/src/main/resources/application.yml#L47`, `application-dev.yml#L24`, `application-prod.yml#L19`.
Spec: TD 5.3, D-83.

## Run the backend locally

Requirements: Docker Desktop, JDK 21. Full steps are in the code repository `README.md`.

```bash
cp deploy/.env.example deploy/.env       # then fill DB_PASSWORD and JWT_SECRET (≥ 32 chars)
docker compose -f deploy/docker-compose.dev.yml up -d   # PostgreSQL+TimescaleDB :5432, Redis :6379

# Windows
.\deploy\run-backend.ps1
# macOS / Linux
set -a && . ./deploy/.env && set +a
cd backend && ./mvnw spring-boot:run -Dspring-boot.run.profiles=dev
```

Check it is up: `GET http://localhost:8080/actuator/health` → `{"status":"UP"}` (public).

### What the `dev` profile gives you

| Feature | `dev` | Note |
|---|---|---|
| Binance sync, backfill, streams, futures metrics | On | Needs internet. First start fills history for some minutes |
| 13 demo pairs | Created and activated on both markets | BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT, DOGEUSDT, ADAUSDT, AVAXUSDT, LINKUSDT, LTCUSDT, BCHUSDT, UNIUSDT, ARBUSDT (Q-05, Q-16) |
| STOMP market topics | On | `MarketHubJob` pushes every 1 s / 2 s |
| Swagger UI | `http://localhost:8080/swagger-ui.html` | OpenAPI JSON at `/v3/api-docs`. Off in `prod` |
| Demo data (`classpath:db/demo`) | Applied | Accounts below |

### Accounts for testing

No password is committed. A seeded account opens only after you put a BCrypt hash (strength 12) of
a password you choose into `deploy/.env`.

| Email | Role | Plan | Hash variable |
|---|---|---|---|
| `admin@cryptopilot.invalid` | ADMIN | — | `ADMIN_PASSWORD_HASH` |
| `demo.trader@cryptopilot.invalid` | TRADER | FREE | `DEMO_PASSWORD_HASH` |
| `trader.free@cryptopilot.invalid` | TRADER | FREE | `DEMO_PASSWORD_HASH` |
| `trader.pro@cryptopilot.invalid` | TRADER | PRO (yearly, from 2026-09-28) | `DEMO_PASSWORD_HASH` |
| `trader.premium@cryptopilot.invalid` | TRADER | PREMIUM (yearly, from 2026-09-28) | `DEMO_PASSWORD_HASH` |

Or register a new account: no mail is sent yet (the email adapter is T-057), so the verification
link never arrives and a self-registered account cannot log in (MSG11). Use the seeded accounts.

Source: `backend/src/main/resources/db/demo/R__demo_dataset.sql`,
`backend/src/main/resources/db/demo/R__demo_plan_accounts.sql`, `deploy/.env.example`.

### Known limits of a local backend

- One instance only: the STOMP broker is in memory (ADR-005, Q-07).
- Futures plans cannot be sized: `leverage_bracket` is empty in every environment until the admin
  screen (T-085) exists, so `POST /plans` with `market=FUTURES` answers 400 `errors.leverage` MSG15
  (D-70). See `modules/trading-plan.md`.
- No email, no push, no payment gateway yet (T-057, T-058, T-067…T-069).

## Request headers

| Header | When | Value |
|---|---|---|
| `Authorization` | Every protected call | `Bearer <accessToken>` |
| `Content-Type` | Every call with a body | `application/json` |
| `X-Correlation-Id` | Optional, every call | `[A-Za-z0-9._:-]{1,64}`. The backend echoes it on the response and puts it in `traceId` of an error. Absent or invalid → the backend generates a UUID v7 |

Source: `backend/src/main/java/com/cryptopilot/common/web/CorrelationIdFilter.java#L55`.

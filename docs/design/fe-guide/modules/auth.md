# Module: auth

Screens SCR-02 … SCR-07 (Security tab). Flow and token rules: [../02-auth.md](../02-auth.md).
Code prefix: `backend/src/main/java/com/cryptopilot/auth/`. Controller: `controller/AuthController.java`.

Shared types:

```ts
interface MessageResponse { messageCode: string }

interface SessionResponse {
  accessToken: string;
  accessTokenExpiresAt: string;   // ISO 8601 UTC, now + 15 min
  refreshToken: string;
  refreshTokenExpiresAt: string;  // now + 7 d, or 30 d with rememberMe
  role: 'TRADER' | 'ADMIN';
}
```

Password rule (BR-02), same regex the server uses: `^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,64}$`
(`auth/PasswordPolicy.java#L47`).

---

### POST /auth/register
Status: IMPLEMENTED (develop)
Auth: public
Purpose: Create a TRADER account and send a verification link (UC-01).

Request body:

| Field | Type | Required | Rule → error |
|---|---|---|---|
| `email` | string | yes | not blank → MSG01; email format, ≤ 255 → MSG02 |
| `displayName` | string | yes | not blank, 2–50 chars → MSG01 |
| `password` | string | yes | not blank → MSG01; BR-02 regex → MSG03 |
| `confirmPassword` | string | yes | not blank → MSG01; equal to `password` → MSG03 under key `confirmPasswordMatching` |
| `acceptsDisclaimer` | boolean | yes | must be `true` → MSG01 under key `acceptsDisclaimer` |

Response `201`:

```json
{ "messageCode": "MSG05" }
```

Errors:

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01/02/03 | Field rules above | Under each field |
| 409 | `EMAIL_ALREADY_REGISTERED` | MSG04 | Email taken (case-insensitive) | Under email |

FE notes: MSG05 needs `{email}` from the form. The account is created even if mail fails; send the
user to a "check your mailbox" view with a resend action. No mail is delivered yet (T-057).
Source: `auth/controller/AuthController.java#L72`; `auth/dto/request/RegisterRequest.java#L24`. Spec: SRS 3.2.1, UC-01, BR-01, BR-02.

---

### POST /auth/verify-email
Status: IMPLEMENTED (develop)
Auth: public
Purpose: Confirm the address from the mailed link (UC-02).

| Field | Type | Required | Rule |
|---|---|---|---|
| `token` | string | yes | not blank → MSG01 |

Response `200`: `{ "messageCode": "MSG06" }`

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `TOKEN_INVALID_OR_EXPIRED` | MSG07 | Unknown, used or expired (24 h) | MSG07 + "Resend verification email" |
| 409 | `EMAIL_ALREADY_VERIFIED` | MSG07 | Account already verified | MSG07 + link to log in |

FE notes: read the token from the link's query string on SCR-03 and POST it; call once (React
StrictMode double effects would consume the token, then the second call fails).
Source: `auth/controller/AuthController.java#L88`; `auth/dto/request/VerifyEmailRequest.java#L13`. Spec: SRS 3.2.2, UC-02.

---

### POST /auth/resend-verification
Status: IMPLEMENTED (develop)
Auth: public
Purpose: Send a new verification link (SRS 3.2.2).

| Field | Type | Required | Rule |
|---|---|---|---|
| `email` | string | yes | not blank → MSG01; format → MSG02 |

Response `202`: `{ "messageCode": "MSG05" }` — the same whatever the address holds.

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01/02 | Bad email |

FE notes: SRS asks for a 60 s cooldown and MSG46 after 5 per day; the server does **not** refuse yet
(T-105). Disable the button for 60 s on the client.
Source: `auth/controller/AuthController.java#L105`; `auth/dto/request/ResendVerificationRequest.java#L11`. Spec: SRS 3.2.2, D-57, A-36.

---

### POST /auth/login
Status: IMPLEMENTED (develop)
Auth: public
Purpose: Sign in and open a session (UC-03).

| Field | Type | Required | Rule |
|---|---|---|---|
| `email` | string | yes | not blank → MSG01; format → MSG02 |
| `password` | string | yes | not blank → MSG01 |
| `rememberMe` | boolean | no | default `false`; `true` → 30-day refresh token |

Response `200`:

```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiJ9.<payload>.<signature>",
  "accessTokenExpiresAt": "2026-09-21T10:15:00Z",
  "refreshToken": "<43 url-safe characters>",
  "refreshTokenExpiresAt": "2026-09-28T10:00:00Z",
  "role": "TRADER"
}
```

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 401 | `INVALID_CREDENTIALS` | MSG08 | Wrong email or password | Inline; do not say which |
| 429 | `LOGIN_TEMPORARILY_LOCKED` | MSG09 | 5th consecutive failure and during the 15 min; `messageArgs[0]` minutes left | Inline |
| 403 | `ACCOUNT_NOT_ACTIVE` | MSG10 | LOCKED or BANNED; `messageArgs[0]` = status | Inline |
| 403 | `EMAIL_NOT_VERIFIED` | MSG11 | Not verified | Inline + resend link |

FE notes: a 401 here is **not** "session expired" — do not run the refresh logic on this endpoint.
Route TRADER → SCR-08, ADMIN → SCR-33. The mobile app registers its FCM token after this (`POST
/me/devices`).
Source: `auth/controller/AuthController.java#L125`; `auth/dto/request/LoginRequest.java#L28`; `auth/dto/response/SessionResponse.java#L30`. Spec: SRS 3.2.3, UC-03, BR-03, BR-06.

---

### POST /auth/refresh
Status: IMPLEMENTED (develop)
Auth: public (the refresh token is the credential)
Purpose: Rotate the refresh token and get a new access token.

| Field | Type | Required | Rule |
|---|---|---|---|
| `refreshToken` | string | yes | not blank → MSG01 |

Response `200`: `SessionResponse` (same shape as login).

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 401 | `SESSION_EXPIRED` | MSG44 | Token unknown, expired, already used (whole session revoked) or revoked | Drop tokens, MSG44, SCR-04 |

FE notes: single-flight (one refresh at a time, see 02-auth). Replace both tokens.
Source: `auth/controller/AuthController.java#L142`; `auth/dto/request/RefreshRequest.java#L17`. Spec: SRS 3.2.3, TD 7.15, D-26.

---

### POST /auth/logout
Status: IMPLEMENTED (develop)
Auth: public (works with an expired access token)
Purpose: End the session of the given refresh token (UC-05).

| Field | Type | Required | Rule |
|---|---|---|---|
| `refreshToken` | string | yes | not blank → MSG01 |
| `fcmToken` | string | no | ≤ 512 → MSG01. Mobile: deactivates this device's push if it belongs to the account |

Response `204`, no body — always, whether the token was valid or not.

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01 | Missing token |

FE notes: clear local tokens even if the call fails (network). Return to SCR-01.
Source: `auth/controller/AuthController.java#L189`; `auth/dto/request/LogoutRequest.java#L22`. Spec: SRS 3.2.3, 3.2.5, D-34.

---

### POST /auth/forgot-password
Status: IMPLEMENTED (develop)
Auth: public
Purpose: Request a password reset link (UC-04, SCR-05).

| Field | Type | Required | Rule |
|---|---|---|---|
| `email` | string | yes | not blank → MSG01; format → MSG02 |

Response `202`: `{ "messageCode": "MSG12" }` — same for every address.

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01/02 | Bad email |

FE notes: no server throttle (A-28); disable the button for a few seconds. No mail yet (T-057).
Source: `auth/controller/AuthController.java#L164`; `auth/dto/request/ForgotPasswordRequest.java#L16`. Spec: SRS 3.2.4, UC-04.

---

### POST /auth/reset-password
Status: IMPLEMENTED (develop)
Auth: public
Purpose: Set a new password from the reset link (SCR-06).

| Field | Type | Required | Rule |
|---|---|---|---|
| `token` | string | yes | not blank → MSG01 |
| `newPassword` | string | yes | not blank → MSG01; BR-02 → MSG03 |
| `confirmPassword` | string | yes | not blank → MSG01; equal → MSG03 under `confirmPasswordMatching` |

Response `200`: `{ "messageCode": "MSG13" }`

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `TOKEN_INVALID_OR_EXPIRED` | MSG07 | Link unknown, used or older than 30 min | MSG07 + "Request a new link" |
| 400 | `VALIDATION_FAILED` / `PASSWORD_POLICY_VIOLATION` | MSG01/MSG03 | Field rules | Under fields |

FE notes: every session of the account is revoked; clear local tokens and go to SCR-04.
Source: `auth/controller/AuthController.java#L180`; `auth/dto/request/ResetPasswordRequest.java#L17`. Spec: SRS 3.2.4, BR-04.

---

### PUT /me/password
Status: IMPLEMENTED (develop)
Auth: trader or admin (bearer)
Purpose: Change the password of the signed-in account (UC-07, Security tab of SCR-07).

| Field | Type | Required | Rule |
|---|---|---|---|
| `currentPassword` | string | yes | not blank → MSG01 |
| `newPassword` | string | yes | not blank → MSG01; BR-02 → MSG03 |
| `confirmPassword` | string | yes | not blank → MSG01; equal → MSG03 under `confirmPasswordMatching` |

Response `200`: `{ "messageCode": "MSG14" }`

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `CURRENT_PASSWORD_INCORRECT` | MSG08 | Wrong current password | Under current password; stay signed in (D-35) |
| 400 | `VALIDATION_FAILED` / `PASSWORD_POLICY_VIOLATION` | MSG01/03 | Field rules | Under fields |
| 401 | `AUTHENTICATION_REQUIRED` | MSG44 | No valid session | Refresh, then MSG44 |

FE notes: all **other** sessions end; this one keeps working. Repeated wrong current passwords may
revoke the session (A-30) — then the next call is 401.
Source: `auth/controller/PasswordChangeController.java#L52`; `auth/dto/request/ChangePasswordRequest.java#L22`. Spec: SRS 3.2.5, UC-07, D-33, D-35.

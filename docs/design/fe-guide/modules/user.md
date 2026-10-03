# Module: user

Screen SCR-07 (Profile, Risk, Notifications tabs) and the mobile device registration.
All endpoints: TRADER only (ADMIN gets 403; an admin uses only `PUT /me/password`, see auth).
Code prefix: `backend/src/main/java/com/cryptopilot/user/`.

---

### GET /me/profile
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: Read the Profile and Notifications tabs (UC-06, UC-08).

Request: none.

Response `200`:

```json
{
  "email": "trader.pro@cryptopilot.invalid",
  "displayName": "Pro Trader",
  "avatarUrl": null,
  "defaultCapital": "1000",
  "defaultRiskPercent": "1.000",
  "tradingStyle": "SWING",
  "riskProfile": "CONSERVATIVE",
  "notifyEmail": true,
  "notifyPush": true
}
```

```ts
interface ProfileResponse {
  email: string;
  displayName: string;
  avatarUrl: string | null;            // always null until T-101
  defaultCapital: string | null;       // USDT
  defaultRiskPercent: string | null;   // percent, 0.1–10
  tradingStyle: 'SCALPING' | 'DAY' | 'SWING' | 'POSITION' | null;
  riskProfile: 'CONSERVATIVE' | 'BALANCED' | 'AGGRESSIVE';
  notifyEmail: boolean;
  notifyPush: boolean;
}
```

| Status | `code` | MSG | When |
|---|---|---|---|
| 401 | `AUTHENTICATION_REQUIRED` | MSG44 | No valid session |

FE notes: cache as the "me" query; invalidate after any `/me/*` write. `defaultCapital` and
`defaultRiskPercent` pre-fill SCR-17.
Source: `user/controller/ProfileController.java#L52`; `user/dto/response/ProfileResponse.java#L30`. Spec: SRS 3.2.5, UC-06.

---

### PUT /me/profile
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: Save the Profile tab.

**Full replacement:** a field sent as `null` or left out is cleared (except `displayName`, which is
required). Always send the whole form.

| Field | Type | Required | Rule → error |
|---|---|---|---|
| `displayName` | string | yes | not blank, 2–50 → MSG01 |
| `defaultCapital` | decimal string | no | > 0, ≤ 20 integer digits, ≤ 8 decimals → MSG15 |
| `defaultRiskPercent` | decimal string | no | 0.1–10, ≤ 3 decimals → MSG15 |
| `tradingStyle` | `TradingStyle` | no | enum; unknown value → 400 `errors.tradingStyle` "is not readable" |

Response `200`: `{ "messageCode": "MSG14" }`

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01/MSG15 | Field rules |
| 401 | `AUTHENTICATION_REQUIRED` | MSG44 | No valid session |

FE notes: changing `tradingStyle` changes the setup score preset on the next `GET /analysis` (T-109).
Avatar upload is not available (T-101).
Source: `user/controller/ProfileController.java#L62`; `user/dto/request/UpdateProfileRequest.java#L37`; `user/entity/UserProfile.java#L117`. Spec: SRS 3.2.5, UC-06.

---

### PUT /me/notification-preferences
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: Save the Notifications tab (UC-08). In-app notifications are always on.

| Field | Type | Required | Rule |
|---|---|---|---|
| `email` | boolean | yes | not null → MSG01 |
| `push` | boolean | yes | not null → MSG01 |

Response `200`: `{ "messageCode": "MSG14" }`

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01 | Missing value |

FE notes: the response fields are named `notifyEmail`/`notifyPush`, the request fields `email`/`push`.
Source: `user/controller/ProfileController.java#L74`; `user/dto/request/NotificationPreferencesRequest.java#L17`. Spec: SRS 3.2.5, UC-08.

---

### GET /me/risk-profile
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: The caller's risk profile and its parameters (BR-66).

Response `200`:

```json
{
  "riskProfile": "CONSERVATIVE",
  "riskPerTradePercent": "0.5",
  "maxFuturesLeverage": 3,
  "maxTotalOpenRiskPercent": "2"
}
```

```ts
interface RiskProfileResponse {
  riskProfile: 'CONSERVATIVE' | 'BALANCED' | 'AGGRESSIVE';
  riskPerTradePercent: string;
  maxFuturesLeverage: number;
  maxTotalOpenRiskPercent: string;
}
```

FE notes: use `maxFuturesLeverage` as the leverage slider's soft limit on SCR-17 (above it the plan
gets a HIGH_LEVERAGE warning, not a refusal).
Source: `user/controller/RiskProfileController.java#L62`; `user/dto/response/RiskProfileResponse.java#L15`. Spec: BR-66, D-64.

---

### PUT /me/risk-profile
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: Choose a risk profile.

| Field | Type | Required | Rule |
|---|---|---|---|
| `riskProfile` | `RiskProfile` | yes | not null → MSG01 |
| `confirmAggressive` | boolean | no | must be `true` when `riskProfile` is `AGGRESSIVE` |

Response `200`: `{ "messageCode": "MSG14" }`

| Status | `code` | MSG | When | Show |
|---|---|---|---|---|
| 400 | `RISK_PROFILE_CONFIRMATION_REQUIRED` | MSG48 | AGGRESSIVE without `confirmAggressive: true` | MSG48 confirm dialog |
| 400 | `VALIDATION_FAILED` | MSG01 | Missing profile | Under field |

FE notes: show MSG48 **before** sending when the user picks AGGRESSIVE, then send with
`confirmAggressive: true`. The 400 is the server-side guard.
Source: `user/controller/RiskProfileController.java#L73`; `user/dto/request/ChooseRiskProfileRequest.java#L15`. Spec: SRS 3.2.5, BR-66, D-65.

---

### GET /me/risk-questionnaire
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: The 6 questions of the risk questionnaire v1 (BR-67).

Response `200` (first question shown):

```json
{
  "questions": [
    {
      "code": "CAPACITY_SHARE_OF_SAVINGS",
      "group": "CAPACITY",
      "text": "What share of your savings is the capital you trade with?",
      "options": [
        { "code": "MORE_THAN_HALF", "text": "More than half" },
        { "code": "A_FIFTH_TO_HALF", "text": "Between a fifth and a half" },
        { "code": "LESS_THAN_A_FIFTH", "text": "Less than a fifth" }
      ]
    }
  ]
}
```

```ts
interface RiskQuestionnaireResponse { questions: RiskQuestion[] }
interface RiskQuestion { code: string; group: 'CAPACITY' | 'ATTITUDE'; text: string; options: RiskAnswerOption[] }
interface RiskAnswerOption { code: string; text: string }
```

FE notes: static for version 1 — cache for the session. Points are not sent.
Source: `user/controller/RiskProfileController.java#L45`; `user/dto/response/RiskQuestionnaireResponse.java#L10`. Spec: BR-67, TD 7.16.

---

### POST /me/risk-questionnaire
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: Score the answers and suggest a profile. Saves nothing.

| Field | Type | Required | Rule |
|---|---|---|---|
| `answers` | object `{ [questionCode]: optionCode }` | yes | every question answered, no unknown key or option → MSG01 (no `errors` map) |

```json
{ "answers": { "CAPACITY_SHARE_OF_SAVINGS": "LESS_THAN_A_FIFTH", "CAPACITY_EMERGENCY_FUND": "OVER_6_MONTHS" } }
```

Response `200`:

```json
{ "capacityScore": 8, "attitudeScore": 6, "suggestedProfile": "BALANCED" }
```

```ts
interface RiskSuggestionResponse { capacityScore: number; attitudeScore: number; suggestedProfile: RiskProfile }
```

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01 | Missing/unknown answer (banner; check all answered before sending) |

FE notes: show the suggestion; the profile changes only after the user picks one and `PUT
/me/risk-profile` (SRS 3.2.5).
Source: `user/controller/RiskProfileController.java#L54`; `user/dto/request/RiskQuestionnaireAnswersRequest.java#L14`; `user/dto/response/RiskSuggestionResponse.java#L12`. Spec: BR-67.

---

### POST /me/devices
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: Register the mobile app's FCM token for push (UC-08).

| Field | Type | Required | Rule |
|---|---|---|---|
| `fcmToken` | string | yes | not blank, ≤ 512 → MSG01 |
| `platform` | `DevicePlatform` | yes | `ANDROID` or `IOS` → MSG01 |

Response `201`:

```json
{ "deviceId": "0199a1b2-7c3d-7e4f-8a9b-0c1d2e3f4a5b", "platform": "ANDROID", "active": true }
```

```ts
interface DeviceResponse { deviceId: string; platform: 'ANDROID' | 'IOS'; active: boolean }
```

| Status | `code` | MSG | When |
|---|---|---|---|
| 400 | `VALIDATION_FAILED` | MSG01 | Field rules |

FE notes: idempotent by token — call after every login and on FCM token refresh; the same token
returns the same device. Keep `deviceId` for the delete below. Push sending itself is T-058.
Source: `user/controller/DeviceController.java#L51`; `user/dto/request/RegisterDeviceRequest.java#L20`; `user/dto/response/DeviceResponse.java#L18`. Spec: SRS 3.2.5, D-34.

---

### DELETE /me/devices/{deviceId}
Status: IMPLEMENTED (develop)
Auth: trader
Purpose: Deactivate a device of the caller.

Path: `deviceId` UUID.

Response `204`.

| Status | `code` | MSG | When |
|---|---|---|---|
| 404 | `RESOURCE_NOT_FOUND` | MSG41 | Not a device of this account |
| 400 | `VALIDATION_FAILED` | MSG01 | `deviceId` not a UUID |

FE notes: at logout prefer sending `fcmToken` to `POST /auth/logout`, which works even with an
expired access token.
Source: `user/controller/DeviceController.java#L66`. Spec: SRS 3.2.5, D-34.

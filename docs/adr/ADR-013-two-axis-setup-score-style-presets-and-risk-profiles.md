# ADR-013 — Two-axis model: style presets for the setup score, risk profiles for capital management

**Status:** Accepted
**Date:** 2026-09-26
**Deciders:** BE1, BE2, FE, DO; supervisor
**Related:** BR-13, BR-21, BR-29, BR-30, SRS 3.2.5, SRS 3.3.5; TECHNICAL_DESIGN 7.4, 7.5; CURRENT_STATE D-53, Q-01, A-07, A-34; tasks T-027, T-028, T-029, T-033, T-035, T-037, T-103
**Amended:** 2026-09-26 — directional components by market, `dominant_side`, one style field (`trading_style`), BR-29 thresholds from the risk profile, the alert minimum not used in v1

## Context
BR-13 fixes one set of weights for everyone (Spot 35/30/15/20, Futures 30/25/15/15/15), and Q-01 left the weights and
the scoring table of each component unconfirmed. TECHNICAL_DESIGN 7.4 had proposed a two-direction score with a
`setup_bias` column (A-07). The team and the supervisor wanted a score that follows the trader's style, and a way to
fit capital management to the trader's appetite for risk, without making the score itself subjective.

## Decision
Two independent axes. The **style preset** decides how the setup is scored; the **risk profile** decides how much
capital goes into a setup and when to warn. The risk profile never enters the score.

### Definitions
- **Component score**: a 0–100 score of one BR-13 component (trend, momentum, volume, level, derivatives), computed
  from the market data of one symbol and one timeframe. It carries no direction (no LONG/SHORT field, never negative).
  The directional components — trend, momentum and level — are read on the LONG side only on Spot, because a Spot plan
  is LONG only (BR-21), so a strong down-trend scores low and so does a close just under resistance; on Futures they
  take `max(LONG, SHORT)`, so a strong down-trend scores as high as its mirror up-trend. Volume and derivatives are not
  directional and are the same on both markets (TECHNICAL_DESIGN 7.4).
- **Style preset**: a primary timeframe plus a weight for each component. Three presets: `SCALPING`, `DAY_TRADING`,
  `SWING`. Each preset has a version, starting at `v1`.
- **Setup score**: the weighted sum of the component scores under one preset. 0–100, no direction.
- **Risk profile**: `CONSERVATIVE`, `BALANCED`, `AGGRESSIVE`. Used only for capital management and warnings.

### Invariant rules
1. The setup score depends only on market data and the style preset. The risk profile is **never** an input of the score.
   *(Setup score chỉ phụ thuộc dữ liệu thị trường và preset phong cách. Hồ sơ rủi ro KHÔNG BAO GIỜ là đầu vào khi tính score.)*
2. Component scores and the setup score have no direction. Direction is not part of the score.
   *(Điểm thành phần và setup score không có hướng. Hướng không nằm trong score.)*
   Note: `dominant_side` (Futures only: LONG, SHORT or NEUTRAL, the winning side of the trend component, NEUTRAL when
   both sides are equal) is information that accompanies the score, not part of it, and is not stored; it does not
   contradict A-07. It is computed at read time and returned beside the Futures setup score; Spot has no such field.
   *(dominant_side là thông tin đi kèm, không phải một phần của score, không lưu trữ; không mâu thuẫn với A-07.)*
3. Component scores are computed once per symbol + timeframe and stored. The setup score is computed at read time by
   applying the preset's weights. No setup score is stored per user.
   *(Điểm thành phần tính 1 lần cho mỗi symbol + timeframe và được lưu. Setup score được tính lúc đọc bằng cách áp trọng số preset. Không lưu setup score riêng cho từng user.)*
4. The weights of a preset add up to exactly 100%.
   *(Trọng số trong 1 preset cộng lại đúng 100%.)*
5. Every setup score returned carries the preset name and version.
   *(Mọi setup score trả ra phải kèm tên preset + version.)*
6. Preset weights and risk profile parameters live in configuration and change without a code change.
   *(Trọng số preset và tham số hồ sơ rủi ro nằm trong cấu hình, đổi được mà không sửa code.)*
7. Users cannot customise weights or risk parameters in the MVP. Customisation is a later phase (related to Q-04).
   *(Người dùng KHÔNG được tùy chỉnh trọng số hay tham số rủi ro ở MVP. Tùy chỉnh để giai đoạn sau (liên quan Q-04).)*

### Risk profiles v1 (fixed values)

| Parameter | CONSERVATIVE | BALANCED | AGGRESSIVE |
|---|---|---|---|
| Risk per trade (% of capital) | 0.5 | 1 | 2 |
| Minimum setup score to alert (in configuration, no feature uses it in v1) | 75 | 65 | 55 |
| Maximum futures leverage | 3x | 5x | 10x |
| Maximum total open risk (% of capital) | 2 | 4 | 6 |

- Hard ceiling: no profile may exceed the `AGGRESSIVE` values.
- BR-29 thresholds come from the user's profile: OVERSIZED_POSITION is raised when the plan's risk per trade exceeds the
  profile's, HIGH_LEVERAGE when the leverage exceeds the profile's maximum. The seeded fixed 2 % and 20x are replaced
  (the hard ceiling is 10x); T-037 does it and updates `SeedDataTest` with it.
- The minimum setup score to alert is kept in configuration; no feature uses it in v1 (no alert type is added).
- Default profile of a new user: `BALANCED`.
- The profile is determined by an onboarding questionnaire of 5–7 questions in two groups: financial capacity to bear
  losses, and attitude to risk. The user may change the profile; switching to `AGGRESSIVE` shows a warning.
- Risk per trade follows the fixed fractional method (Vince 1990) in the common 0.5–2% range; position size and
  R-multiples follow Tharp 1999. The other three values: v1, chosen from experience, adjusted through configuration.

### Style selection: one field
The preset is selected by the existing profile field `trading_style` (SRS 3.2.5). It is the only source: there is no
second style field. Mapping v1: `SCALPING` → SCALPING, `DAY` → DAY_TRADING, `SWING` → SWING, `POSITION` → SWING until a
POSITION preset exists; not set → DAY_TRADING, which is also the preset of any read without a user. Whether the enum is
renamed or a mapping class translates it is T-103's choice, as long as one source remains.

### Style presets v1

| Preset | Primary timeframe | Timeframe used in v1 |
|---|---|---|
| SCALPING | 5m | **15m** — BR-08 stores and streams 15m, 1h, 4h, 1d only (T-020, T-021); 15m is the nearest available. The preset switches to 5m when 5m is ingested |
| DAY_TRADING | 1h | 1h |
| SWING | 4h | 4h |

Weights v1 (%). The derivatives component exists on Futures only, so each preset has a Spot and a Futures column; each
column adds up to 100 and no weight is 0 or above 40. All are v1 values, chosen from experience, adjusted through
configuration.

| Component | SCALPING Spot | SCALPING Futures | DAY_TRADING Spot | DAY_TRADING Futures | SWING Spot | SWING Futures |
|---|---|---|---|---|---|---|
| Trend T | 20 | 15 | 35 | 30 | 40 | 35 |
| Momentum Mo | 40 | 35 | 30 | 25 | 20 | 15 |
| Volume V | 25 | 20 | 15 | 15 | 10 | 10 |
| Level L | 15 | 10 | 20 | 15 | 30 | 25 |
| Derivatives D | — | 20 | — | 15 | — | 15 |

Reasons, one per weight:
- SCALPING T 20 / 15: a trend matters less over a few candles; kept as context so the score does not fight the move.
- SCALPING Mo 40 / 35: momentum is what a short trade lives on, so it carries the most weight (the ceiling on Spot).
- SCALPING V 25 / 20: BR-13 has no volatility component; volume relative to its average is the short-term activity
  signal it does have.
- SCALPING L 15 / 10: support and resistance on 15m candles are close together and broken often.
- SCALPING D — / 20: funding and a 1-hour open interest change are short-term flows, relevant at this horizon.
- DAY_TRADING T 35 / 30: equal footing with momentum; these are the BR-13 weights unchanged.
- DAY_TRADING Mo 30 / 25: balances the trend (BR-13 weights).
- DAY_TRADING V 15 / 15: confirmation only (BR-13 weights).
- DAY_TRADING L 20 / 15: levels on 1h candles frame an intraday trade (BR-13 weights).
- DAY_TRADING D — / 15: BR-13 weight.
- SWING T 40 / 35: a trade held for days depends on the trend first (the ceiling on Spot).
- SWING Mo 20 / 15: momentum on 4h candles swings inside a trend; secondary.
- SWING V 10 / 10: one candle's volume says little over days; the lowest weight, but not zero.
- SWING L 30 / 25: price structure — the swing support and resistance of T-026 — sets entry and stop for a swing trade.
- SWING D — / 15: funding is paid several times over a multi-day hold.

### A-07
Closed as **no direction**. There is no `setup_bias` column or field in v1, and no migration adds one — in T-026 or
any other task — because direction is not part of the score (invariant rule 2).

## Consequences
- Component scores are computed once per (pair, market, timeframe) whatever the number of users; a score costs a
  weighted sum at read time.
- Trend, momentum and level keep their one-sided readings: LONG only on Spot, `max(LONG, SHORT)` on Futures. Volume and
  derivatives have one direction-free form (TECHNICAL_DESIGN 7.4, with a worked example).
- BR-13, BR-29 and SRS 3.2.5 change; recorded as A-34 and carried into the SRS by T-097.
- The risk profile field, the `trading_style` → preset mapping and the onboarding questionnaire are a new task, T-103;
  T-014 stays DONE.
- The minimum setup score to alert is in configuration and no feature uses it in v1: the alert types of SRS 3.4.2 have no
  setup score condition and none is added.
- A user who picks SCALPING gets 15m scores until 5m candles are ingested; the preset reports the timeframe it used.

## Alternatives considered
- One fixed set of weights for everyone: contradicts the goal of a score that follows the trading style.
- Mixing risk appetite into the score: the same setup would get different scores, which cannot be verified.
- Letting users edit the weights in the MVP: more scope, scores become hard to compare; left for a later phase.
- A directional score: direction is kept apart from judging the quality of a setup.

Why this one:
- An objective score: the same data and the same preset give every user the same score, so it can be verified,
  backtested and cached.
- Risk appetite decides how much capital goes into a setup, not whether the setup is good. This is how investment
  platforms use a risk profile (to allocate capital).
- Risk per trade follows the fixed fractional method, inside the common 0.5–2% range.
- Computing component scores once and weighting at read time avoids work proportional to users × symbols.
- Three presets plus three profiles are six small configurations, instead of nine weight tables if the axes were mixed.

## References
- Wilder, J. W. (1978). *New Concepts in Technical Trading Systems*. Trend Research. (RSI in the momentum component.)
- Tharp, V. K. (1999). *Trade Your Way to Financial Freedom*. McGraw-Hill. (Position sizing, R-multiples.)
- Vince, R. (1990). *Portfolio Management Formulas*. Wiley. (Fixed fractional risk per trade.)

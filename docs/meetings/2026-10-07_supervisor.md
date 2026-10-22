# Supervisor meeting — 2026-10-07

Status: team lead's summary, recorded 2026-10-22 (D-112). Not the supervisor's wording. Supervisor confirmation: optional, not received.

| Item | Value |
|---|---|
| Date | 2026-10-07 (team lead) |
| Attendees | not recorded |
| GY-03 | "Trading Plan and entry timing deviation: a plan must say when it is no longer valid, how far a late entry moved from the plan in R, and the simulated fills must behave like the exchange" — team lead's summary |
| Design | D-111, D-112 |

## BTC example (team lead's summary)

LONG, entry 100,000, stop loss 98,000, take profit 106,000, risk 100 USDT.

| Fill | Deviation | Quantity | Risk/reward |
|---|---|---|---|
| 100,000 | 0R | 0.05 | 3.0 |
| 101,000 | 0.5R | 0.0333 | 1.67 |
| 102,000 | 1.0R | 0.025 | 1.0 |

The thresholds 0.25R (confirm) and 0.75R (block) are design values of D-111. They are not part of the summary.

## Search done 2026-10-22

Terms: `GY-`, supervisor, giảng viên, GVHD, biên bản, meeting, minutes, 2026-10-07, 07/10, 106,000, 0.0333, entry timing.

Searched every file and the full history of every branch of the documents repository, including every version of the SRS `.docx` (deleted and renamed files included), and the full history of every branch of the code repository.

Result: nothing about this meeting dated before 2026-10-22. The only hits were unrelated: SRS text "agreed with the supervisor" and durations in minutes, a delivery plan dated from 07/10/2026, test timestamps and golden data in the code, and the `MarketStreamSupervisor` class. The first record of GY-03 and of the BTC example is the GY-03 design commit of 2026-10-22.

There are no written minutes of the 2026-10-07 meeting, so this record holds only the team lead's summary (Q-73, answered by D-112). Supervisor feedback items other than GY-03 were not summarised and are not recorded here.

# CryptoPilot — local project documents

> These documents are kept out of the **code** repository by `.git/info/exclude`, installed by
> `docs/tools/setup-local.sh` (macOS/Linux/Git Bash) or `docs/tools/setup-local.ps1` (Windows).
>
> They are shared through a **second, private repository** (`cryptopilot-docs`) whose git dir is
> `.docs.git/` in this same folder, driven by `./docs.sh` or `.\docs.ps1`. Setup and the daily
> commands are in **[BOOTSTRAP.md](BOOTSTRAP.md)**.
>
> Not a shared drive, and not a branch of the code repository. A drive cannot merge
> `CURRENT_STATE.md`, which is appended to at the end of every session, so one person's session log
> would silently overwrite another's; a branch would put these files on GitHub for anyone who opens
> the code repository.

Crypto Trading Support System — capstone project, 09/2026 → 03/2027.

CryptoPilot helps traders analyse the Binance Spot and USDⓈ-M Futures markets, plan trades with explicit risk control, practise through simulated execution, and review the results in a trading journal.

**CryptoPilot is a decision-support and paper-trading system.** It never executes real orders, never uses exchange API keys, never holds funds or digital assets, and never gives investment advice.

---

## Documents

| File | Owns | Read it when |
|---|---|---|
| `CLAUDE.md` | Rules for AI coding agents | Start of every AI session |
| `CURRENT_STATE.md` | Project status: tasks, decisions, open questions, session log | Start of every session; updated at the end of every session |
| `docs/srs/` | **What** the system must do — SRS Report 3 (business rules BR-xx, use cases UC-xx, screens SCR-xx, non-screen functions NSF-xx, messages MSGxx) | Whenever a task references an SRS id |
| `docs/design/TECHNICAL_DESIGN.md` | **How** it is built — architecture, folder structure, design patterns, algorithms, APIs, test strategy | Before writing code in a new area |
| `docs/design/CryptoPilot_Logical_Model.txt` | Data structure (38 entities, Mermaid ER) | Any task that touches data |
| `docs/design/context-diagram.txt` | System boundary and external entities (Mermaid) | Integration work |
| `docs/adr/` | One decision per file, with consequences and alternatives | Before changing an architectural choice |
| `docs/test/` | Test plan, golden data description, traceability matrix | Test work |

**Conflict rule:** SRS business rules > technical design > logical model > code. A deviation is never fixed silently in code; it is recorded in `CURRENT_STATE.md` section 5 and approved by the team first.

---

## Architecture in one paragraph

A modular monolith (Java 21 + Spring Boot 4.1: REST + STOMP WebSocket + schedulers) plus one stateless AI Service (Node.js) that talks to the LLM provider. One PostgreSQL database with TimescaleDB for time series, Redis for latest prices. The backend is the only database writer. Code is organised package by module, then by layer (`controller`, `service`, `repository`, `entity`, `dto`, `calculator`, …) across twelve modules plus `common`; a module writes only its own tables, calls others through their root-package `XxxApi`, and reacts to them through events stored by the Spring Modulith event publication registry (transactional outbox). Spring Modulith and ArchUnit tests fail the build when a boundary is crossed. Details and the rationale: `docs/design/TECHNICAL_DESIGN.md` sections 1–4.

---

## Repository layout

```
cryptopilot/
├── CLAUDE.md              CURRENT_STATE.md              README.md
├── docs/                  srs · design · adr · test
├── backend/               Spring Boot (Maven): com.cryptopilot.<module>.<layer>
├── ai-service/            Node.js + TypeScript, stateless
├── web/                   React + TypeScript + Vite
├── mobile/                Flutter
├── deploy/                docker-compose, environment files
└── tools/                 golden indicator data, scripts
```

Full tree with every module folder: `docs/design/TECHNICAL_DESIGN.md` section 4.

---

## Getting started (developer)

```bash
sh docs/tools/setup-local.sh            # once per clone (Windows: powershell -ExecutionPolicy Bypass -File docs\tools\setup-local.ps1)
cp deploy/.env.example deploy/.env      # fill in local values; never commit deploy/.env
docker compose -f deploy/docker-compose.dev.yml up -d
cd backend && ./mvnw spring-boot:run -Dspring-boot.run.profiles=dev
```

Prerequisites, seed data and the demo account are described in T-004 and T-007 of `CURRENT_STATE.md`.

---

## Working agreement

- Branches: `main` (protected) ← `develop` ← `feature/T-xxx-short-name`; pull request with one reviewer and green CI.
- Commits: Conventional Commits with a `Refs: T-xxx` footer. No AI attribution lines.
- A task is done only when the Definition of Done in `CLAUDE.md` section 6 is met.
- Anything not in the SRS needs a new task row and a decision entry before it is built.

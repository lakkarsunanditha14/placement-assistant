# Phase 0 — Requirements Traceability & Architecture Baseline

This file is the contract. Every later phase is checked against it.

## 1. What this system is

A personal placement assistant for one student. It reads **explicitly authorized**
placement sources, understands what each message means, extracts opportunities,
decides eligibility with deterministic rules, tracks deadlines, interprets
shortlist/selection documents, and — only with two explicit approvals — prepares
and submits an application form.

## 2. What this system is NOT

- A general social-media agent
- A mass-application bot
- A general job-search engine
- A resume builder
- An interview platform
- A multi-agent demo where agents add no real value

## 3. Non-negotiable rules

| # | Rule |
|---|------|
| 1 | Placement sources are **strictly read-only**. No send/reply/post/react/edit/delete/forward. |
| 2 | Only sources the student explicitly authorized may be read. |
| 3 | Unknown personal information is **never guessed**. Ask the user. |
| 4 | **Silence is never approval.** |
| 5 | CAPTCHA / OTP / password / access controls are **never bypassed**. |
| 6 | Preparing an application requires **Gate 1** (explicit yes). |
| 7 | Submitting an application requires **Gate 2** (explicit yes). |
| 8 | Reusable answers are stored only with **explicit memory consent**. |
| 9 | AI-generated answers are **labelled** and shown for review. |
| 10 | Message facts, research facts and unverified facts are kept **separate**. |

## 4. Division of responsibility

AI is **never** used for: arithmetic rules, permissions, approval gates,
deadline computation, required-field validation, database transactions.

## 5. Architecture (modular monolith — not microservices)

**Deliberately excluded until proven necessary:** vector DB, multi-agent systems,
LangChain-heavy orchestration, fine-tuning, custom OCR models, Kubernetes,
microservices, Redis/Celery.

## 6. Application state machine (Phase 11+)

State is persisted in PostgreSQL so a restart or browser crash can never cause a
duplicate action.

## 7. Field source labels (Phase 13+)

`VERIFIED_PROFILE` · `USER_PROVIDED` · `AI_GENERATED` · `UNCERTAIN` · `MANUAL_ACTION_REQUIRED`

## 8. Roadmap

| Phase | Build | Definition of done |
|---|---|---|
| 0 | Requirements traceability + architecture | Scope/boundaries/stack understood |
| 1 | Local setup + FastAPI + Next.js + PostgreSQL | Runs in VS Code |
| 2 | Profile + permissions | Trusted profile and source authorization work |
| 3 | Mock/local adapter | Pipeline testable without Telegram |
| 4 | Telegram read-only adapter | Real messages in, no write path |
| 5 | Message storage/normalization | Provenance and processing states work |
| 6 | Claude classification/extraction | Validated structured output |
| 7 | Eligibility engine | Explainable deterministic results |
| 8 | Feed/reminders | Deadline and pending-action reminders work |
| 9 | PDF/DOCX/image pipeline | Lists interpreted before name status |
| 10 | Company research | Source distinction + uncertainty |
| 11 | Gate 1 + workflow | Preparation impossible without approval |
| 12 | Playwright form inspection | Supported forms inspected safely |
| 13 | Autofill + unknown questions | Only trusted fields filled |
| 14 | Memory consent | Reusable answers require consent |
| 15 | Validation + review | Full form review works |
| 16 | Gate 2 + submission | Submission impossible without approval |
| 17 | Tracking/failure/manual states | All outcomes visible |
| 18 | Security/audit/deployment | Secrets, permissions and logs stable |
| 19 | Scale only if justified | Queues/vector search only when needed |

**Rule: do not start a phase before the previous phase's definition of done is met.**

## 9. Mandatory safety tests (added progressively, never removed)

- unauthorized source is rejected
- no source write operation exists anywhere in the codebase
- low-confidence content cannot start an application
- no Gate 1 -> no preparation
- no Gate 2 -> no submission
- unknown answers are never fabricated
- memory requires consent
- CAPTCHA/OTP/password are never bypassed
- a completed form never auto-submits
- inactivity never becomes approval
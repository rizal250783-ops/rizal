# AO-360 — AO Achievement Dashboard (PT BPRS Haji Miskin)

## Problem Statement
Internal banking performance-management web app "AO-360" (Phase I) for PT BPRS Haji Miskin (Direktur: HENDRI KAMAL). Monitors Account Officer achievement, portfolio quality, NPF, and collection activity documentation. Concept: Mengukur → Mengevaluasi → Meningkatkan.

## Architecture
- Backend: FastAPI (`/app/backend/server.py`), calc engine (`calculations.py`), photo/storage (`storage_util.py`), demo seed (`seed.py`). MongoDB via motor.
- Frontend: React (CRA + craco) + Tailwind + recharts + lucide, `src/pages/*`, `src/components/*`, `src/lib/*`.
- Auth: JWT (Bearer token in localStorage + httpOnly cookie fallback). RBAC roles: direktur, admin, ao_lending, ao_funding, pic_remedial.
- Object storage: Emergent object storage with server-side watermark (PIL), EXIF extraction + GPS fallback, HEIC/compress.

## Personas
Direktur (read-only executive), Admin (full), AO Lending, AO Funding, PIC Remedial.

## Core Requirements (static)
Role dashboards; divide-by-zero → N/A (22a); performance score with weight normalization; NPF ratio+score(cap 150)+quantitative status (40a/41a); ranking with tie-breaker + N/A at bottom; portfolio kolektibilitas 1-5; collection multi-photo (≤5) + watermark + GPS EXIF fallback; user mgmt + role history; target/achievement per period YYYY-MM; performance setting versioned (weights total 100%) + parameters; data import preview/confirm, export XLSX, backup (no password_hash) + restore (force password reset); audit log; login security (policy, lockout 5x/15min, force change).

## Implemented (2026-09-03)
- ALL Phase I modules built from scratch and tested. Backend 45/45 pytest passed. Frontend 100% (all role flows, dashboards, charts, leaderboard, portfolio, NPF, collection, users, targets, performance settings, data mgmt, audit, system settings).
- 12 demo users seeded + targets/achievements/portfolio. Example numbers verified: Rizky lending 113% Excellent; NPF 2.68% Sehat, score ~112%.
- Fixes applied & verified: period filter destructuring, file endpoint JWT auth, collection no-photo validation, NPF RBAC, import 400 for unsupported type, CORS regex, idempotent admin password.

## Backlog / Next (P1/P2)
- P1: import/confirm for User/Target/Achievement/Remedial types (currently portfolio only).
- P1: restore snapshot safety (real auto-backup before wipe).
- P2: YTD trend charts & historical ranking views; export/backup filename period suffix on frontend; short-lived signed file tokens instead of ?auth=; shadcn date/file inputs.
- Phase II: AO Productivity Monitor (structure ready, not built).

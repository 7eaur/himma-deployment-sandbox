# CHANGELOG

## [Corrective Recovery — UI / Media / Supervisor / Student] — 2026-08-26

**Branch:** `recovery/ui-media-admin-overhaul`  
**Implementation checkpoint:** `7dbc52bcc70a5768c81cd04065be00f1949c429d`  
**Evidence run:** GitHub Actions #171 / `32928214424` — Backend ✅ Frontend ✅ Integration/Playwright ✅

### Recovered

- Restored approved canonical assessment/activity interaction semantics instead of generic multiple-choice rendering.
- Connected real approved education images/audio and fixed media-package path resolution; added byte-level regression checks.
- Rebuilt assessment UI for image/listen/sequence/build-word/read-aloud families.
- Rebuilt student journey/dashboard and child-focused public landing.
- Added recording/re-record/send and manual audio-review states without false calibrated-ASR claims.
- Protected supervisor routes and standardized visible terminology to `المشرف` while preserving the legacy internal `researcher` identifier for compatibility.
- Added supervisor profile/password/add-supervisor settings.
- Added secure six-digit numeric student-code create/manual/edit/regenerate workflows and student name/status management.
- Added adaptive reinforcement mapping-gap recovery: student hold state, approved same-level supervisor options, written reason, audit logging, and student resume.
- Fixed adaptation/reinforcement concurrency behavior so duplicate creation conflicts do not roll back prior adaptive state.
- Preserved approved content gaps as neutral; no replacement audio is invented.
- Added full Chromium Playwright path with screenshots through reinforcement assignment/resume and live reports.
- Visual review found and fixed the adaptive-hold state so it is a real scoped full-screen dialog instead of an unstyled block leaking the underlying activity.

### Remaining external blockers

This recovery does not close P07 speech analysis. Real provider approval, representative recordings, confidence calibration, child-audio retention policy, and approved missing source audio remain open as recorded in `OPEN_ITEMS.md`.

---

## [P01 Audit] — 2026-08-17

### المرحلة: P01 (AUDIT_ONLY)

**الحكم على Stage 02:** REJECTED

**السبب:**
- `STAGE_02_REVIEW.md` ادّعى نجاح E2E وMinIO لكن:
  - `vertical-slice.spec.ts` يفشل بـ Timeout 30s
  - `storage.py` يستخدم mock-s3-bucket.local
  - CI لا يشغل PostgreSQL حقيقياً

**التوثيق المُنشأ:**
- `docs/ops/stages/P01/CURRENT_STATE_AUDIT.md`
- `docs/ops/stages/P01/BASELINE_SNAPSHOT.json`
- `docs/ops/stages/P01/TRACEABILITY_MATRIX.md`
- `docs/ops/stages/P01/GAP_REGISTER.md`
- `docs/ops/stages/P01/EVIDENCE_INDEX.md`
- `docs/ops/stages/P01/RECOVERY_RECOMMENDATION.md`
- `docs/ops/RESUME_HERE.md` (محدَّث)
- `docs/ops/STATUS.md` (محدَّث)
- `docs/ops/progress.json` (محدَّث)

---

## [Stage 01] — 2026-08-10

**الحكم:** ACCEPTED  
**Commit:** `ac3cae2`  
**التفاصيل:** إغلاق بوابة المرحلة الأولى (النواة والأمن) عبر gate-stage-01.md

---

## [Stage 02] — 2026-08-11 → مرفوضة

**HEAD عند الإغلاق المزعوم:** `88c0e71`  
**الحكم الفعلي:** REJECTED  
**السبب:** أدلة وهمية — انظر P01 GAP_REGISTER

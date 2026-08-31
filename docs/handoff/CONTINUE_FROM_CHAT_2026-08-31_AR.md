# HIMMA — CONTINUE FROM THIS CHAT — 2026-08-31

> هذا ملف تسليم سريع للمحادثة/الوكيل التالي. لا يستبدل المرجع الكامل، بل يضع آخر حالة فعلية ثم يوجّه إلى ملفات الاستمرارية الأساسية.
>
> **قاعدة البداية:** لأن إضافة هذا الملف نفسها تحرّك HEAD، لا تعتبر أي SHA مذكور هنا HEAD الحالي تلقائيًا. افحص الفرع وGitHub Actions أولًا، ثم أكمل من أول gap حقيقي فقط.

## 1) المستودع وفرع العمل

- Repository: `7eaur/himma-`
- Working branch: `recovery/ui-media-admin-overhaul`
- لا تعدّل مباشرة:
  - `stage/04-production-slice`
  - `stage/02-content`
- ممنوع: `reset --hard`, `clean -fd`, force push أو حذف تاريخ مقبول.
- لا تعلن PASS/إغلاق دون SHA دقيق + Workflow run + jobs.
- لا تدمج/تطلق production دون موافقة صريحة من المستخدم.

## 2) آخر حالة تحققت قبل إنشاء ملف التسليم هذا

### HEAD الذي شوهد قبل كتابة هذا الملف

`d1e702558b5a51c55c1c1a3d2fc5691579b4ecd1`

Commit:

`docs(m09): record release-readiness evidence`

Main Quality Gate لنفس SHA:

- Himma CI — Quality Gate #497
- Run ID: `33344886935`
- Status: `SUCCESS`

هذا commit توثيقي. لا يوجد Responsive run خاص به لأنه لم يغيّر UI.

### آخر executable M09 baseline موثّق

`9f4389d83f751910daf605e1c37b4232b5b3ae93`

Commit:

`feat(m09): add backup restore release gate`

Evidence:

- Main Quality Gate #496 — Run `33344517705`: backend ✅ frontend ✅ integration/Playwright ✅
- Himma M09 — Release Readiness Gate #1 — Run `33344517713`: ✅ SUCCESS

Relevant responsive evidence:

- Responsive Visual Gate #95 — Run `33344062713` on `a5545a1425cc99891972e2ec55b290198cb98034`: ✅ SUCCESS
- commits التالية حتى `9f4389d...` كانت operational/docs وليست UI changes.

## 3) اقرأ هذه الملفات بالترتيب

1. `START_HERE_AR.md`
2. `docs/ops/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-08-31_AR.md`
3. `docs/ops/STATUS.md`
4. `docs/ops/progress.json`
5. `docs/ops/M09_RELEASE_UAT_RUNBOOK.md`
6. `docs/ops/M09_RELEASE_READINESS_EVIDENCE_2026-08-31.md`
7. `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`
8. `docs/specs/SOURCE_OF_TRUTH.md`

لا تعتمد على ذاكرة المحادثة أو أسماء الملفات بدل قراءة الكود/الاختبارات/CI الفعلية.

## 4) الحالة التنفيذية الحالية المختصرة

- Original approved content: 105 items.
- Runtime additions: +20 reinforcement.
- Runtime total: **125**.
- Reinforcement total: **35**.
- Skills: **44**.
- Student QX / child-clear question experience: closed baseline.
- Generated educational sequence assets: 10, wired to runtime.
- Reinforcement lifecycle + source-core verification/escalation: implemented baseline.
- Reports/exports/per-skill descriptive evidence: implemented baseline.
- R1 early promotion policy: implemented/tested.
- R2 active-session handoff after promotion: fixed.
- R3 supervisor-authorized pre/post retake history/index behavior: fixed baseline.
- R4 responsive primary student CTA regression coverage: added.
- M08 real production speech analysis: **PENDING / EXTERNAL-GATED**.
- M09 Release/UAT: **IN PROGRESS**; infrastructure readiness/backup slice green, complete single-candidate journey UAT remains open.

## 5) الأكاديمي/التكيف — لا ترجع لقواعد أقدم

Placement:

- 100 = readiness 20 + word building/reading 40 + fluency/comprehension 40.
- readiness <12/20 forces L1.
- total <50 → L1.
- 50..<80 → L2 subject to reading gates.
- L3 requires its approved gates; لا تختلق text-accuracy threshold غير معتمد.

Learning bands:

- >=80 PASS
- 70..<80 GUIDED_RETRY
- <70 WEAKNESS_EVENT → targeted reinforcement

Mastery evidence:

- newest 3 valid attempts only: 50/30/20.
- neutral media/audio evidence excluded from denominator/mastery.

### R1 current promotion policy

L1/L2 can promote early only when all gates pass:

- at least 6 completed Core activities;
- mastery >=85;
- critical-skill floor >=70;
- required critical-skill coverage complete;
- no unresolved reinforcement or supervisor-review blocker;
- promotion is one level only.

Automatic demotion remains disabled. L3 still requires full evidence before journey completion/posttest readiness.

**لا تعيد القاعدة التاريخية التي كانت تمنع أي promotion قبل 10/10 في L1/L2.**

## 6) Reinforcement lifecycle

Runtime contract:

`weakness → mapped same-level reinforcement → reinforcement completion → reopen source core → verify failed source steps → verified/escalated → continue`

- no random reinforcement;
- no cross-level fallback;
- neutral media-gap skip is not failed evidence;
- verification is bounded (default 2 rounds) then escalates to supervisor.

Key files:

- `services/api/reinforcement_cycles.py`
- `services/api/db/reinforcement_models.py`
- `services/api/adaptation_runtime.py`
- `services/api/reinforcement_review.py`

## 7) R2 active-session handoff

Key bridge:

- `services/api/activities_v4.py`

When early promotion closes the previous level session, `/activities/session/{id}/next` must continue on the newly created active session and return its authoritative `session_id`. Never submit the next activity back to the closed session.

## 8) Student UX / assessment neutrality

Learning activities may use contextual hints/retry/success/error/stars.
Formal pre/post tests remain neutral per item:

- no correctness feedback after each item;
- no answer-revealing hints;
- no per-item stars/reward signals before completion.

Student UI baseline includes explicit child-clear instructions, answers below the prompt, touch-friendly controls, subtle sounds with mute, reduced-motion support, and no permanent mascot side rail.

## 9) Audio / M08

Static audio inventory:

- existing: 50
- missing exact assets: `موز`, `سَا`
- target: 52

`HIMMA_TEMP_AUDIO_SKIP` is testing-only and academically neutral. Trial/production startup fails closed if this bypass is enabled.

Target speech architecture remains:

`Reference-Guided Arabic Reading Analysis = ASR + reference alignment + C/D/I/S + phonemic helper evidence`

M08 is not complete because provider connection, calibration, privacy/retention and production acceptance remain unresolved/external-gated. Do not claim it production-ready.

## 10) M09 what is already closed internally

Already proved/green:

- `/health` liveness retained.
- `/ready` readiness added for critical config + PostgreSQL + Redis + private S3/MinIO.
- sanitized dependency failure output.
- trial/production fail-closed guard for temporary audio bypass and short API secret.
- executable PostgreSQL backup/restore with integrity/count verification.
- executable private object-store backup/isolated restore with SHA-256 verification.
- dedicated M09 Release Readiness Gate is green.
- runbook exists: `docs/ops/M09_RELEASE_UAT_RUNBOOK.md`.

Do **not** redo this work unless a current regression proves it broken.

## 11) M09 remaining open work — next conversation starts here

Primary next slice:

1. Build/execute a complete **single-candidate full-journey UAT** using the real runtime path:
   `supervisor/student setup → pretest → placement → learning → weakness/reinforcement/verification where applicable → L1/L2 transitions → L3 full evidence → posttest authorization/completion → reports → XLSX/PDF exports`.
2. Reuse scenarios already proved by existing same-SHA Quality Gate; add only the missing cross-stage end-to-end assertions.
3. Produce exact evidence: test name, SHA, workflow run IDs, jobs, artifacts/screenshots if applicable.
4. Then continue M09 remaining internal release closure:
   - monitoring/request correlation/support readiness;
   - privacy/data-retention final approval for real study data;
   - rollback/release checklist and final acceptance evidence.
5. Keep M08 separate until external gates are available.
6. Acquire only exact approved static audio `موز` and `سَا`; no fake/substitute assets.
7. If substantial UI/runtime changes occur, run Main Quality Gate + Responsive Visual Gate and visually inspect artifacts before claiming closure.

## 12) Source authority

At conflict, follow:

1. latest explicit user instruction;
2. approved client content / original reference materials;
3. current code + tests + same-SHA CI evidence;
4. current Source of Truth / decision docs;
5. corrective roadmap;
6. older historical docs;
7. prototype/screenshots only as UX reference, never as authority to overwrite runtime semantics.

Historical docs saying runtime = 123/+18 only are stale. Current runtime = 125/+20 additions.

## 13) Definition of a valid continuation

A new conversation is ready to continue only after it:

- reads the files in section 3;
- checks current branch HEAD after this handoff commit;
- checks GitHub Actions for that HEAD;
- fixes any current failure before new work;
- states which exact open M09 gap it will close next;
- does not silently change academic/content semantics;
- does not claim M08 complete;
- does not claim M09 complete until full UAT + release closure evidence exist.

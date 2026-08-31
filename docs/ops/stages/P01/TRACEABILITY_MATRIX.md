# مصفوفة التتبع - TRACEABILITY MATRIX
# P01 Audit — 17 أغسطس 2026

## Routes × API × DB × Status

| المسار (Route) | Method | API Endpoint | الجدول (Table) | الدور | الحالة |
|---|---|---|---|---|---|
| `/` | GET | — | — | Public | production |
| `/admin/login` | GET/POST | `POST /auth/login` | users | Researcher | partial (307 loop) |
| `/admin` | GET | — | — | Researcher | partial |
| `/admin/students` | GET | `GET /researcher/students` | students | Researcher | partial |
| `/admin/students/new` | GET/POST | `POST /researcher/students` | students | Researcher | partial |
| `/admin/students/[id]` | GET | `GET /researcher/students` | students | Researcher | partial |
| `/admin/audio-review` | GET | `GET /review/pending-audio` | audio_submissions | Researcher | partial |
| `/admin/account` | GET | `GET /me` | users | Researcher | partial |
| `/student/login` | GET/POST | `POST /auth/student-login` | students | Student | partial |
| `/student` | GET | `GET /profile` + `GET /assessment/active` | students, sessions | Student | partial |
| `/student/session/[id]` | GET | `GET /assessment/session/:id/next` | sessions, items, attempts | Student | partial |
| `/student/activity/[id]` | GET | — | — | Student | placeholder |

## API Endpoints × DB Tables

| Endpoint | Method | Tables | Auth | Idempotency | Status |
|---|---|---|---|---|---|
| `/auth/login` | POST | users | None | No | production |
| `/auth/student-login` | POST | students | None | No | production |
| `/auth/logout` | POST | — | Cookie | No | production |
| `/me` | GET | users | Researcher | No | production |
| `/profile` | GET | students | Student | No | production |
| `/researcher/students` | GET/POST | students | Researcher | No | partial |
| `/assessment/start` | POST | sessions | Student | Needs check | partial |
| `/assessment/active` | GET | sessions | Student | No | partial |
| `/assessment/session/:id/next` | GET | sessions, items, attempts | Student | No | partial |
| `/assessment/session/:id/attempt/:item/submit` | POST | attempts, responses, audio_submissions | Student | Partial | partial |
| `/assessment/session/:id/finish` | POST | sessions, students | Student | No | partial |
| `/review/pending-audio` | GET | audio_submissions, responses | Researcher | No | partial |
| `/review/audio/:id/grade` | POST | audio_reviews | Researcher | No | partial |
| `/recordings/init` | POST | — | Student | No | mock |
| `/recordings/complete` | POST | — | Student | No | mock |
| `/recordings/stream/:key` | GET | — | Researcher | No | mock |

## DB Tables × Migrations

| الجدول | Migration | الحالة |
|---|---|---|
| users | 0001_initial | production |
| students | 0001_initial | production |
| audit_logs | 0001_initial | production |
| content_items | 0002_content_models | partial |
| content_steps | 0002_content_models | partial |
| content_options | 0002_content_models | partial |
| assessment_sessions | 0002_content_models | partial |
| attempts | 0002_content_models | partial |
| attempt_responses | 0002_content_models | partial |
| audio_submissions | 0003_audio_review | partial |
| audio_reviews | 0003_audio_review | partial |

## UC Scenarios × Implementation

| UC | الوصف | Backend | Frontend | E2E Test | الحالة |
|---|---|---|---|---|---|
| UC-01 | Admin Login | production | partial | FAILED | partial |
| UC-02 | Create Student | production | partial | Not tested | partial |
| UC-03 | Student Login | production | partial | Not tested | partial |
| UC-04 | Start Pretest | production | partial | Not tested | partial |
| UC-05 | Answer 30 Questions | production | partial | Not tested | partial |
| UC-06 | Audio Recording | partial | partial | Not tested | partial |
| UC-07 | Audio Upload to MinIO | mock | partial | Not tested | mock |
| UC-08 | Researcher Review Audio | partial | partial | Not tested | partial |
| UC-09 | Grade Audio | partial | partial | Not tested | partial |
| UC-10 | Level Assignment | production | partial | Not tested | partial |
| UC-11 | Student Progress View | missing | placeholder | Not tested | missing |
| UC-12 | Researcher Dashboard | partial | partial | Not tested | partial |

## Assets × Usage

| الأصل | الوجود | الاستخدام في الواجهة | الملاحظة |
|---|---|---|---|
| `/public/brand/logo-gradient.svg` | موجود | `/student/session` header | partial |
| `/public/brand/logo-flat.svg` | موجود | غير مستخدم | unused |
| `/public/brand/logo-navy.svg` | موجود | غير مستخدم | unused |
| `/public/characters/boy-welcome.png` | موجود | `/student/session` | partial |
| `/public/characters/boy-success.png` | موجود | `/student/session` completion | partial |
| `/public/characters/boy-explain.png` | موجود | `AssessmentRunner` | partial |
| `/public/characters/boy-encourage.png` | موجود | غير مستخدم | unused |
| `/public/characters/boy-try-again.png` | موجود | غير مستخدم | unused |
| `assets/audio/HIMMA_AUDIO_V1/` | موجود (50 عنصر) | غير مرتبطة بالكود | missing link |
| `assets/education/` (60 صورة) | موجودة | غير مستخدمة في UI | missing link |
| `packages/content/src/catalog.json` | موجود | seed.py يقرأه | partial |

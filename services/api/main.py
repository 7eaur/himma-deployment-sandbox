import os
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
from protected import router as protected_router
from assessment import router as assessment_router
from assessment_retake import router as assessment_retake_router
from temporary_audio_skip import router as temporary_audio_skip_router
from review import router as review_router
from recordings import router as recordings_router
from activities_v4 import router as activities_router
from adaptation import router as adaptation_router
from adaptation_runtime import router as adaptation_runtime_router
from reinforcement_review import router as reinforcement_review_router
from media import router as media_router
from speech_analysis import router as speech_analysis_router
from journey import router as journey_router
from reports import router as reports_router
from skill_reports import router as skill_reports_router
from readiness import readiness_report
from runtime_flags import validate_runtime_safety
from db.diag_admin import collect_admin_diag
from db.sandbox_bootstrap import ensure_sandbox_admin
from seed_all import run_seed_all


# Trial/production must fail closed while the temporary audio bypass is enabled.
# Dependency availability is intentionally handled by /ready rather than here so
# the process can remain live while an external dependency is recovering.
validate_runtime_safety()

app = FastAPI(
    title="Himma API Service",
    description="API service for Himma Educational Platform",
    version="0.1.0",
)


@app.on_event("startup")
def bootstrap_sandbox_runtime() -> None:
    if os.getenv("ENV", "").strip().lower() == "sandbox":
        run_seed_all()
        ensure_sandbox_admin()


# CORS — allows the Next.js dev server and production URL
_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(protected_router)
app.include_router(journey_router)
# R3: owns /assessment/start so completed pre/post assessments can only be
# repeated through a durable supervisor authorization with a written reason.
app.include_router(assessment_retake_router)
# TEMPORARY: this router must precede assessment_router so its finish endpoint
# can apply a neutral denominator only when explicit audio-skip markers exist.
app.include_router(temporary_audio_skip_router)
app.include_router(assessment_router)
app.include_router(activities_router)
app.include_router(adaptation_router)
app.include_router(adaptation_runtime_router)
app.include_router(reinforcement_review_router)
app.include_router(media_router)
app.include_router(review_router)
app.include_router(recordings_router)
app.include_router(speech_analysis_router)
app.include_router(reports_router)
app.include_router(skill_reports_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "himma-api"}


@app.get("/ready")
def readiness_check(response: Response):
    report = readiness_report()
    if report["status"] != "ready":
        response.status_code = 503
    return report


@app.get("/debug/admin-diag")
def debug_admin_diag():
    return collect_admin_diag()

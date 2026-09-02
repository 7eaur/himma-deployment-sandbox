import os

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from auth import router as auth_router
from protected import router as protected_router
from assessment import router as assessment_router
from assessment_view import router as assessment_view_router
from assessment_retake import router as assessment_retake_router
from temporary_audio_skip import router as temporary_audio_skip_router
from review import router as review_router
from recordings import router as recordings_router
from activities_v4 import router as activities_router
from learning_experience import router as learning_experience_router
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
from db.sandbox_bootstrap import ensure_sandbox_runtime


validate_runtime_safety()

app = FastAPI(
    title="Himma API Service",
    description="API service for Himma Educational Platform",
    version="0.1.0",
)


@app.on_event("startup")
def bootstrap_sandbox_runtime() -> None:
    ensure_sandbox_runtime()


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
app.include_router(assessment_retake_router)
app.include_router(temporary_audio_skip_router)
app.include_router(assessment_router)
app.include_router(assessment_view_router)
app.include_router(learning_experience_router)
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

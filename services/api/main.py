import os
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
from protected import router as protected_router
from assessment import router as assessment_router
from assessment_completion import router as assessment_completion_router
from assessment_view import router as assessment_view_router
from assessment_retake import router as assessment_retake_router
from review import router as review_router
from recordings import router as recordings_router
from audio_review_navigation import router as audio_review_navigation_router
from activity_runtime import router as activities_router
from learning_experience import router as learning_experience_router
from adaptation import router as adaptation_router
from adaptation_runtime import router as adaptation_runtime_router
from reinforcement_review import router as reinforcement_review_router
from content_preview import router as content_preview_router
from media import router as media_router
from speech_analysis import router as speech_analysis_router
from journey import router as journey_router
from reports import router as reports_router
from skill_reports import router as skill_reports_router
from admin_notifications import router as admin_notifications_router
from readiness import readiness_report
from runtime_flags import validate_runtime_safety


# Runtime configuration still fails closed for unsafe provider/test settings.
# Student audio has no bypass path: submitted recordings are reviewed by the
# supervisor until the approved automatic speech model is integrated.
validate_runtime_safety()

app = FastAPI(
    title="Himma API Service",
    description="API service for Himma Educational Platform",
    version="0.1.0",
)

_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Critical assessment/activity URLs each have one mounted owner; the async audio
# navigation overlay is intentionally registered before the historical activity
# runtime for the GET status/progress/next routes. Submission remains owned by
# activity_runtime, while review-pending navigation is non-blocking.
app.include_router(auth_router)
app.include_router(protected_router)
app.include_router(journey_router)
app.include_router(assessment_retake_router)
app.include_router(assessment_completion_router)
app.include_router(assessment_router)
app.include_router(assessment_view_router)
app.include_router(learning_experience_router)
app.include_router(audio_review_navigation_router)
app.include_router(activities_router)
app.include_router(adaptation_router)
app.include_router(adaptation_runtime_router)
app.include_router(reinforcement_review_router)
app.include_router(content_preview_router)
app.include_router(media_router)
app.include_router(review_router)
app.include_router(recordings_router)
app.include_router(speech_analysis_router)
app.include_router(reports_router)
app.include_router(skill_reports_router)
app.include_router(admin_notifications_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "himma-api"}


@app.get("/ready")
def readiness_check(response: Response):
    report = readiness_report()
    if report["status"] != "ready":
        response.status_code = 503
    return report

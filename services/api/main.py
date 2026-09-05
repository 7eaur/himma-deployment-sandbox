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
from activity_runtime import router as activities_router
from learning_experience import router as learning_experience_router
from adaptation import router as adaptation_router
from adaptation_runtime import router as adaptation_runtime_router
from reinforcement_review import router as reinforcement_review_router
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

# Critical assessment/activity URLs each have one mounted owner; helper modules
# may be reused as services but never decide behavior by router registration order.
app.include_router(auth_router)
app.include_router(protected_router)
app.include_router(journey_router)
app.include_router(assessment_retake_router)
app.include_router(assessment_completion_router)
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
app.include_router(admin_notifications_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "himma-api"}


def _sandbox_content_diagnostics() -> None:
    """Temporary sanitized diagnostics for the disposable deployment sandbox."""
    try:
        from db.database import SessionLocal
        from db.models import ContentItem

        db = SessionLocal()
        try:
            items = db.query(ContentItem).all()
            pretest = [item for item in items if item.kind == "pretest_question"]
            learning = [item for item in items if item.kind in {"core_activity", "reinforcement_activity"}]
            posttest = [item for item in items if item.kind == "posttest_question"]
            diagnostics = {
                "total": len(items),
                "reinforcement": sum(item.kind == "reinforcement_activity" for item in items),
                "pretest": len(pretest),
                "learning": len(learning),
                "posttest": len(posttest),
                "student_v2_mismatch": sum(
                    (item.template_data or {}).get("student_experience_version") != "HIMMA-STUDENT-EXPERIENCE-2.0"
                    for item in items
                ),
                "db_runtime_mismatch": sum(
                    ((item.template_data or {}).get("db_runtime") or {}).get("version") != "HIMMA-DB-RUNTIME-1.0"
                    for item in items
                ),
                "pretest_version_mismatch": sum(
                    (item.template_data or {}).get("pretest_experience_version") != "HIMMA-PRETEST-2026-09-01"
                    or ((item.template_data or {}).get("pretest_experience") or {}).get("version") != "HIMMA-PRETEST-2026-09-01"
                    for item in pretest
                ),
                "learning_version_mismatch": sum(
                    (item.template_data or {}).get("learning_experience_version") != "HIMMA-LEARNING-2026-09-01-R2"
                    or ((item.template_data or {}).get("learning_experience") or {}).get("version") != "HIMMA-LEARNING-2026-09-01-R2"
                    for item in learning
                ),
                "posttest_version_mismatch": sum(
                    (item.template_data or {}).get("posttest_experience_version") != "HIMMA-POSTTEST-2026-09-01"
                    or ((item.template_data or {}).get("posttest_experience") or {}).get("version") != "HIMMA-POSTTEST-2026-09-01"
                    for item in posttest
                ),
                "learning_round_mismatch": sum(
                    len(((item.template_data or {}).get("learning_experience") or {}).get("rounds") or []) != len(item.steps)
                    for item in learning
                ),
            }
            print(f"Sandbox content diagnostics: {diagnostics}", flush=True)
        finally:
            db.close()
    except Exception as exc:
        print(f"Sandbox content diagnostics failed: {type(exc).__name__}", flush=True)


@app.get("/ready")
def readiness_check(response: Response):
    report = readiness_report()
    if report["status"] != "ready":
        if os.environ.get("ENV", "").strip().lower() == "sandbox":
            print(f"Sandbox readiness diagnostics: {report['checks']}", flush=True)
            if report.get("checks", {}).get("content") != "ok":
                _sandbox_content_diagnostics()
        response.status_code = 503
    return report

"""P07 speech worker entrypoint.

Usage:
    python speech_worker.py --once
    python speech_worker.py --poll-seconds 3

The worker discovers uploaded audio that has no queue row, then processes due
jobs. It never fabricates ASR results when the provider is not configured.
"""

from __future__ import annotations

import argparse
import os
import time

from db.database import SessionLocal
from db.models import AudioSubmission
from db.speech_models import SpeechAnalysisJob
from speech_pipeline import claimable_job_ids, enqueue_submission, process_job


def discover_jobs(db, limit: int = 100) -> int:
    existing = db.query(SpeechAnalysisJob.submission_id)
    submission_ids = [
        row.id
        for row in db.query(AudioSubmission.id).filter(
            AudioSubmission.status == "uploaded",
            ~AudioSubmission.id.in_(existing),
        ).order_by(AudioSubmission.submitted_at, AudioSubmission.id).limit(limit).all()
    ]
    for submission_id in submission_ids:
        enqueue_submission(db, submission_id)
    if submission_ids:
        db.commit()
    return len(submission_ids)


def run_cycle(limit: int = 10) -> dict[str, int]:
    db = SessionLocal()
    discovered = processed = blocked = 0
    try:
        discovered = discover_jobs(db)
        for job_id in claimable_job_ids(db, limit=limit):
            job = process_job(db, job_id)
            db.commit()
            processed += 1
            if job.status == "blocked_provider":
                blocked += 1
        return {"discovered": discovered, "processed": processed, "blocked_provider": blocked}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Himma speech analysis worker")
    parser.add_argument("--once", action="store_true", help="Run one queue cycle and exit")
    parser.add_argument("--poll-seconds", type=float, default=float(os.getenv("HIMMA_ASR_POLL_SECONDS", "3")))
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    if args.poll_seconds < 0.5:
        parser.error("--poll-seconds must be at least 0.5")
    if args.limit < 1 or args.limit > 100:
        parser.error("--limit must be between 1 and 100")

    while True:
        print(run_cycle(limit=args.limit), flush=True)
        if args.once:
            return
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()

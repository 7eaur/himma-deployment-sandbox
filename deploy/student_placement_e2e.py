"""Isolated hosted placement tests for Himma pretest thresholds.

Creates synthetic students only, completes the full 30-item pretest with two
answer patterns, asserts one is placed in L1 and the other in L2, then
deactivates both students. No access code or secret is printed.
"""

from __future__ import annotations

import os
import sys
import uuid

sys.path.insert(0, "/app/deploy")

from content_runtime import canonical_interaction
from db.database import SessionLocal
from db.models import ContentItem, ContentStep
from student_full_e2e import (
    AUDIO,
    MANY,
    ORDERED,
    SINGLE,
    _cookie,
    _correct_ids,
    _grade_pending,
    _req,
    _upload_audio,
)


def _answer_ids(db, item_id: int, step_id: int, should_be_correct: bool):
    item = db.query(ContentItem).filter(ContentItem.id == item_id).one()
    step = db.query(ContentStep).filter(ContentStep.id == step_id).one()
    ordered = sorted(step.options, key=lambda option: option.order_index)
    interaction, correct = _correct_ids(db, item_id, step_id, learning=False)
    if should_be_correct or interaction in AUDIO:
        return interaction, correct
    if interaction in SINGLE:
        wrong = next((option.id for option in ordered if option.id not in correct), ordered[0].id)
        return interaction, [wrong]
    if interaction in MANY:
        correct_set = set(correct)
        wrong = [option.id for option in ordered if option.id not in correct_set]
        return interaction, wrong[:1] if wrong else correct[:1]
    if interaction in ORDERED:
        reversed_ids = list(reversed(correct))
        if reversed_ids == correct and len(ordered) > 1:
            reversed_ids = [option.id for option in reversed(ordered)]
        return interaction, reversed_ids
    raise RuntimeError(f"unsupported interaction: {interaction}")


def _complete_pattern(base, db, supervisor_cookie, *, label: str, correct_every: int | None, expected_level: int):
    student_id = None
    try:
        status, created, _ = _req(
            base,
            "/researcher/students",
            method="POST",
            cookie=supervisor_cookie,
            payload={"full_name": f"QA {label} {uuid.uuid4().hex[:8]}", "grade_level": 3},
        )
        if status != 201:
            raise RuntimeError(f"{label}: student create failed {status}")
        student_id = int(created["id"])
        status, _, headers = _req(base, "/auth/student-login", method="POST", payload={"access_code": created["access_code"]})
        student_cookie = _cookie(headers)
        if status != 200 or not student_cookie:
            raise RuntimeError(f"{label}: login failed")

        status, session, _ = _req(base, "/assessment/start", method="POST", cookie=student_cookie, payload={"session_type": "pretest"})
        if status != 200:
            raise RuntimeError(f"{label}: pretest start failed {status}")
        session_id = int(session["id"])
        index = 0
        while True:
            status, nxt, _ = _req(base, f"/assessment/session/{session_id}/next", cookie=student_cookie)
            if status != 200:
                raise RuntimeError(f"{label}: next failed {status}")
            if nxt is None:
                break
            item_id = int(nxt["id"])
            step_id = int(nxt["steps"][0]["id"])
            interaction = canonical_interaction(db.query(ContentItem).filter(ContentItem.id == item_id).one())
            should_be_correct = correct_every is not None and index % correct_every == 0
            interaction, ids = _answer_ids(db, item_id, step_id, should_be_correct)
            body = {"step_id": step_id, "elapsed_seconds": 1}
            if interaction in AUDIO:
                audio = _upload_audio(base, session_id, student_cookie)
                body.update({
                    "audio_storage_key": audio["audio_storage_key"],
                    "audio_file_size": audio["audio_file_size"],
                    "audio_mime_type": audio["audio_mime_type"],
                    "audio_duration_seconds": 0.1,
                })
            elif interaction in SINGLE:
                body["selected_option_id"] = ids[0]
            else:
                body["selected_option_ids"] = ids
            status, result, _ = _req(
                base,
                f"/assessment/session/{session_id}/attempt/{item_id}/submit",
                method="POST",
                cookie=student_cookie,
                headers={"Idempotency-Key": f"qa-{label}-{uuid.uuid4().hex}"},
                payload=body,
            )
            if status != 200:
                raise RuntimeError(f"{label}: submit failed {status} {str(result)[:120]}")
            if interaction in AUDIO:
                _grade_pending(base, supervisor_cookie, student_id)
            index += 1
            if index > 40:
                raise RuntimeError(f"{label}: safety bound")

        status, result, _ = _req(base, f"/assessment/session/{session_id}/finish", method="POST", cookie=student_cookie)
        if status != 200:
            raise RuntimeError(f"{label}: finish failed {status} {str(result)[:160]}")
        score = float(result.get("final_score") or 0)
        level = int(result.get("assigned_level") or 0)
        print(f"QA_PLACEMENT_{label}=score:{score}:level:{level}")
        if level != expected_level:
            raise RuntimeError(f"{label}: expected L{expected_level}, got L{level} at score {score}")
        return score
    finally:
        if student_id is not None:
            _req(base, f"/researcher/students/{student_id}", method="PATCH", cookie=supervisor_cookie, payload={"is_active": False})
            print(f"QA_PLACEMENT_{label}_CLEANUP=PASS")


def main():
    domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    admin_user = os.getenv("ADMIN_USERNAME", "")
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    if not domain or not admin_user or not admin_password:
        raise RuntimeError("placement QA requires hosted supervisor credentials")
    base = f"https://{domain}"
    status, _, headers = _req(base, "/auth/login", method="POST", payload={"username": admin_user, "password": admin_password})
    supervisor_cookie = _cookie(headers)
    if status != 200 or not supervisor_cookie:
        raise RuntimeError("placement QA supervisor login failed")

    db = SessionLocal()
    try:
        l1_score = _complete_pattern(base, db, supervisor_cookie, label="L1", correct_every=None, expected_level=1)
        l2_score = _complete_pattern(base, db, supervisor_cookie, label="L2", correct_every=2, expected_level=2)
        if not (l1_score < 50):
            raise RuntimeError(f"L1 score threshold invalid: {l1_score}")
        if not (50 <= l2_score < 80):
            raise RuntimeError(f"L2 score threshold invalid: {l2_score}")
        print("QA_PLACEMENT_THRESHOLDS=PASS")
    finally:
        db.close()


if __name__ == "__main__":
    main()

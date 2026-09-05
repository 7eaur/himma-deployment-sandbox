"""Isolated full student happy-path E2E for the hosted Himma sandbox.

Creates one synthetic student through the supervisor API, completes pretest with
real object-storage audio uploads + supervisor review, completes L3 learning,
enables and completes posttest, verifies terminal profile/journey state, then
deactivates the synthetic student. It never prints access codes or secrets.
"""

from __future__ import annotations

import json
import os
import struct
import urllib.error
import urllib.request
import uuid
from http.cookies import SimpleCookie

import assessment
from content_runtime import canonical_interaction
from db.database import SessionLocal
from db.models import ContentItem, ContentStep

AUDIO = {"read_aloud", "timed_read_aloud"}
SINGLE = {"choose_one", "listen_choose_one", "choose_image", "listen_choose_image"}
MANY = {"choose_many", "listen_choose_many"}
ORDERED = {"sequence", "memory_sequence", "path_sequence", "build_word"}


def _req(base: str, path: str, *, method="GET", payload=None, cookie="", headers=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    merged = {"Accept": "application/json", **(headers or {})}
    if data is not None:
        merged["Content-Type"] = "application/json"
    if cookie:
        merged["Cookie"] = cookie
    req = urllib.request.Request(base + path, data=data, headers=merged, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = raw
            return response.status, body, response.headers
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = raw
        return exc.code, body, exc.headers


def _cookie(headers) -> str:
    jar = SimpleCookie()
    jar.load(headers.get("Set-Cookie", ""))
    return f"access_token={jar['access_token'].value}" if "access_token" in jar else ""


def _wav_bytes() -> bytes:
    rate = 8000
    samples = 800
    pcm = b"\x00\x00" * samples
    return (
        b"RIFF"
        + struct.pack("<I", 36 + len(pcm))
        + b"WAVEfmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
        + b"data"
        + struct.pack("<I", len(pcm))
        + pcm
    )


def _upload_audio(base: str, session_id: int, cookie: str) -> dict:
    boundary = f"----HimmaQA{uuid.uuid4().hex}"
    audio = _wav_bytes()
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="qa.wav"\r\n'
        "Content-Type: audio/wav\r\n\r\n"
    ).encode() + audio + f"\r\n--{boundary}--\r\n".encode()
    headers = {
        "Accept": "application/json",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Idempotency-Key": f"qa-audio-{uuid.uuid4().hex}",
        "Cookie": cookie,
    }
    req = urllib.request.Request(
        base + f"/assessment/session/{session_id}/upload-audio",
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            if response.status != 200:
                raise RuntimeError(f"audio upload status {response.status}")
            return result
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise RuntimeError(f"audio upload failed {exc.code}: {detail[:160]}") from exc


def _correct_ids(db, item_id: int, step_id: int, *, learning: bool) -> tuple[str, list[int]]:
    item = db.query(ContentItem).filter(ContentItem.id == item_id).one()
    step = db.query(ContentStep).filter(ContentStep.id == step_id).one()
    ordered = sorted(step.options, key=lambda option: option.order_index)
    interaction = canonical_interaction(item)
    if interaction in SINGLE:
        correct = next(option.id for option in ordered if option.is_correct)
        return interaction, [correct]
    if interaction in MANY:
        if learning:
            return interaction, [ordered[0].id, ordered[1].id]
        return interaction, [option.id for option in ordered if option.is_correct]
    if interaction in ORDERED:
        if learning:
            return interaction, [option.id for option in ordered]
        return interaction, assessment._expected_order_ids(item, step)
    if interaction in AUDIO:
        return interaction, []
    raise RuntimeError(f"unsupported interaction in QA: {interaction}")


def _grade_pending(base: str, supervisor_cookie: str, student_id: int) -> int:
    status, pending, _ = _req(base, "/review/pending-audio", cookie=supervisor_cookie)
    if status != 200 or not isinstance(pending, list):
        raise RuntimeError(f"pending audio lookup failed: {status}")
    matches = [row for row in pending if row.get("student_id") == student_id]
    if not matches:
        raise RuntimeError("expected pending QA audio was not found")
    for row in matches:
        status, _, _ = _req(
            base,
            f"/review/audio/{row['id']}/grade",
            method="POST",
            cookie=supervisor_cookie,
            payload={
                "is_valid": True,
                "target_units": 1,
                "deletions": 0,
                "substitutions": 0,
                "insertions": 0,
                "pronunciation_notes": "QA synthetic recording",
            },
        )
        if status != 200:
            raise RuntimeError(f"QA audio grade failed: {status}")
    return len(matches)


def _submit_assessment_step(base, db, cookie, supervisor_cookie, student_id, session_id, payload):
    item_id = int(payload["id"])
    step = payload["steps"][0]
    step_id = int(step["id"])
    interaction, ids = _correct_ids(db, item_id, step_id, learning=False)
    body = {"step_id": step_id, "elapsed_seconds": 1}
    if interaction in AUDIO:
        audio = _upload_audio(base, session_id, cookie)
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
        cookie=cookie,
        headers={"Idempotency-Key": f"qa-answer-{uuid.uuid4().hex}"},
        payload=body,
    )
    if status != 200:
        raise RuntimeError(f"assessment submit failed: {status} {str(result)[:160]}")
    if interaction in AUDIO:
        _grade_pending(base, supervisor_cookie, student_id)


def _complete_assessment(base, db, cookie, supervisor_cookie, student_id, session_type):
    status, session, _ = _req(base, "/assessment/start", method="POST", cookie=cookie, payload={"session_type": session_type})
    if status != 200:
        raise RuntimeError(f"{session_type} start failed: {status} {str(session)[:160]}")
    session_id = int(session["id"])

    premature, _, _ = _req(base, f"/assessment/session/{session_id}/finish", method="POST", cookie=cookie)
    if premature != 400:
        raise RuntimeError(f"premature {session_type} finish was not blocked: {premature}")

    iterations = 0
    while True:
        status, nxt, _ = _req(base, f"/assessment/session/{session_id}/next", cookie=cookie)
        if status != 200:
            raise RuntimeError(f"{session_type} next failed: {status} {str(nxt)[:160]}")
        if nxt is None:
            break
        _submit_assessment_step(base, db, cookie, supervisor_cookie, student_id, session_id, nxt)
        iterations += 1
        if iterations > 80:
            raise RuntimeError(f"{session_type} loop exceeded safety bound")

    status, progress, _ = _req(base, f"/assessment/session/{session_id}/progress", cookie=cookie)
    if status != 200 or progress.get("completed_items") != 30:
        raise RuntimeError(f"{session_type} progress incomplete: {status} {progress}")
    status, finished, _ = _req(base, f"/assessment/session/{session_id}/finish", method="POST", cookie=cookie)
    if status != 200:
        raise RuntimeError(f"{session_type} finish failed: {status} {str(finished)[:160]}")
    print(f"QA_FULL_{session_type.upper()}=PASS:score={finished.get('final_score')}:level={finished.get('assigned_level')}")
    return finished


def _complete_learning(base, db, cookie, supervisor_cookie, student_id):
    status, started, _ = _req(base, "/activities/start", method="POST", cookie=cookie)
    if status != 200:
        raise RuntimeError(f"learning start failed: {status} {str(started)[:160]}")
    session_id = int(started["session_id"])
    iterations = 0
    while True:
        status, nxt, _ = _req(base, f"/activities/session/{session_id}/next", cookie=cookie)
        if status != 200:
            raise RuntimeError(f"learning next failed: {status} {str(nxt)[:160]}")
        if nxt is None:
            break
        item = nxt["item"]
        step = nxt["step"]
        item_id = int(item["id"])
        step_id = int(step["id"])
        interaction, ids = _correct_ids(db, item_id, step_id, learning=True)
        body = {"step_id": step_id, "selected_option_ids": ids, "hint_used": False, "elapsed_seconds": 1}
        if interaction in AUDIO:
            audio = _upload_audio(base, session_id, cookie)
            body.update({
                "selected_option_ids": [],
                "audio_storage_key": audio["audio_storage_key"],
                "audio_file_size": audio["audio_file_size"],
                "audio_mime_type": audio["audio_mime_type"],
                "audio_duration_seconds": 0.1,
            })
        status, result, _ = _req(
            base,
            f"/activities/session/{session_id}/attempt/{item_id}/submit",
            method="POST",
            cookie=cookie,
            headers={"Idempotency-Key": f"qa-learn-{uuid.uuid4().hex}"},
            payload=body,
        )
        if status != 200:
            raise RuntimeError(f"learning submit failed: {status} {str(result)[:180]}")
        if interaction in AUDIO:
            _grade_pending(base, supervisor_cookie, student_id)
        iterations += 1
        if iterations > 100:
            raise RuntimeError("learning loop exceeded safety bound")

    status, journey, _ = _req(base, "/journey", cookie=cookie)
    if status != 200 or not journey.get("learning_journey_completed"):
        raise RuntimeError(f"learning journey did not complete: {status} {journey}")
    print(f"QA_FULL_LEARNING=PASS:level={journey.get('current_level')}")


def main():
    domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    admin_user = os.getenv("ADMIN_USERNAME", "")
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    if not domain or not admin_user or not admin_password:
        raise RuntimeError("hosted full QA requires Railway public domain and supervisor seed credentials")
    base = f"https://{domain}"
    db = SessionLocal()
    qa_student_id = None
    supervisor_cookie = ""
    try:
        status, _, headers = _req(base, "/auth/login", method="POST", payload={"username": admin_user, "password": admin_password})
        supervisor_cookie = _cookie(headers)
        if status != 200 or not supervisor_cookie:
            raise RuntimeError("supervisor QA login failed")

        status, created, _ = _req(
            base,
            "/researcher/students",
            method="POST",
            cookie=supervisor_cookie,
            payload={"full_name": f"QA E2E {uuid.uuid4().hex[:8]}", "grade_level": 3},
        )
        if status != 201:
            raise RuntimeError(f"QA student create failed: {status} {str(created)[:160]}")
        qa_student_id = int(created["id"])
        access_code = created["access_code"]
        print(f"QA_FULL_STUDENT_CREATED=id:{qa_student_id}")

        status, _, headers = _req(base, "/auth/student-login", method="POST", payload={"access_code": access_code})
        student_cookie = _cookie(headers)
        if status != 200 or not student_cookie:
            raise RuntimeError("QA student login failed")

        status, profile, _ = _req(base, "/profile", cookie=student_cookie)
        if status != 200 or profile.get("next_action") != "pretest":
            raise RuntimeError(f"initial profile contract failed: {status} {profile}")
        print("QA_FULL_INITIAL_PROFILE=PASS")

        blocked, _, _ = _req(base, "/activities/start", method="POST", cookie=student_cookie)
        if blocked != 409:
            raise RuntimeError(f"learning-before-pretest was not blocked: {blocked}")
        blocked, _, _ = _req(base, "/assessment/start", method="POST", cookie=student_cookie, payload={"session_type": "posttest"})
        if blocked != 409:
            raise RuntimeError(f"posttest-before-pretest was not blocked: {blocked}")
        print("QA_FULL_PRETEST_GUARDS=PASS")

        pre = _complete_assessment(base, db, student_cookie, supervisor_cookie, qa_student_id, "pretest")
        if int(pre.get("assigned_level") or 0) != 3:
            raise RuntimeError(f"all-correct pretest did not place at L3: {pre}")

        blocked, _, _ = _req(base, "/assessment/start", method="POST", cookie=student_cookie, payload={"session_type": "posttest"})
        if blocked != 403:
            raise RuntimeError(f"posttest-before-supervisor-enable was not blocked: {blocked}")
        print("QA_FULL_POSTTEST_LOCK=PASS")

        _complete_learning(base, db, student_cookie, supervisor_cookie, qa_student_id)

        status, _, _ = _req(
            base,
            f"/researcher/students/{qa_student_id}/posttest-access",
            method="POST",
            cookie=supervisor_cookie,
            payload={"enabled": True},
        )
        if status != 200:
            raise RuntimeError(f"posttest enable failed: {status}")
        print("QA_FULL_POSTTEST_ENABLE=PASS")

        _complete_assessment(base, db, student_cookie, supervisor_cookie, qa_student_id, "posttest")

        status, profile, _ = _req(base, "/profile", cookie=student_cookie)
        if status != 200 or profile.get("next_action") != "completed":
            raise RuntimeError(f"terminal student profile failed: {status} {profile}")
        status, journey, _ = _req(base, "/journey", cookie=student_cookie)
        if status != 200 or not journey.get("posttest_completed"):
            raise RuntimeError(f"terminal journey failed: {status} {journey}")
        print("QA_FULL_TERMINAL_STATE=PASS")
        print("QA_FULL_STUDENT_E2E=PASS")
    finally:
        if qa_student_id and supervisor_cookie:
            status, _, _ = _req(
                base,
                f"/researcher/students/{qa_student_id}",
                method="PATCH",
                cookie=supervisor_cookie,
                payload={"is_active": False},
            )
            print(f"QA_FULL_CLEANUP_DEACTIVATE={status}")
        db.close()


if __name__ == "__main__":
    main()

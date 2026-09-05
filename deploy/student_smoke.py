"""Hosted student journey checks for the Railway sandbox.

`smoke` is read-mostly. `deep` additionally exercises resume/progress/next-item
contracts on the currently active sandbox sessions. No answer is submitted and
no access code or secret is printed.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from http.cookies import SimpleCookie

from db.database import SessionLocal
from db.models import AssessmentSession, Student


def request(base: str, path: str, *, method: str = "GET", payload=None, cookie: str = ""):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = body
            return response.status, parsed, response.headers
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        return exc.code, parsed, exc.headers


def cookie_from(headers) -> str:
    raw = headers.get("Set-Cookie", "")
    jar = SimpleCookie()
    jar.load(raw)
    if "access_token" not in jar:
        return ""
    return f"access_token={jar['access_token'].value}"


def main() -> None:
    mode = os.getenv("STUDENT_QA_MODE", "smoke").strip().lower() or "smoke"
    domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if not domain:
        raise RuntimeError("RAILWAY_PUBLIC_DOMAIN is required for hosted checks")
    base = f"https://{domain}"

    db = SessionLocal()
    try:
        students = db.query(Student).filter(Student.is_active.is_(True)).order_by(Student.id).all()
        session_rows = db.query(AssessmentSession).order_by(AssessmentSession.student_id, AssessmentSession.id).all()
        print("QA_DB=RAILWAY_POSTGRES")
        print(f"QA_MODE={mode}")
        print(f"QA_ACTIVE_STUDENTS={len(students)}")
        print(f"QA_SESSIONS={len(session_rows)}")

        status, body, _ = request(base, "/ready")
        print(f"QA_READY={status}:{body.get('status') if isinstance(body, dict) else 'invalid'}")
        if status != 200:
            raise RuntimeError("live API is not ready")

        for path in ("/journey", "/assessment/active", "/activities/status"):
            status, _, _ = request(base, path)
            print(f"QA_UNAUTH_{path.replace('/', '_').strip('_').upper()}={status}")
            if status not in {401, 403}:
                raise RuntimeError(f"unauthenticated endpoint was not rejected: {path}")

        status, _, _ = request(base, "/auth/student-login", method="POST", payload={"access_code": "__INVALID_QA_CODE__"})
        print(f"QA_INVALID_LOGIN={status}")
        if status != 401:
            raise RuntimeError("invalid student access code was not rejected")

        failures: list[str] = []
        for student in students:
            status, _, headers = request(base, "/auth/student-login", method="POST", payload={"access_code": student.access_code})
            print(f"QA_STUDENT_{student.id}_LOGIN={status}")
            token_cookie = cookie_from(headers)
            if status != 200 or not token_cookie:
                failures.append(f"student {student.id}: login")
                continue

            status, body, _ = request(base, "/auth/me", cookie=token_cookie)
            role = body.get("role") if isinstance(body, dict) else None
            print(f"QA_STUDENT_{student.id}_ME={status}:{role}")
            if status != 200 or role != "student":
                failures.append(f"student {student.id}: me")

            status, journey, _ = request(base, "/journey", cookie=token_cookie)
            if isinstance(journey, dict):
                print(f"QA_STUDENT_{student.id}_JOURNEY={status}:pre={journey.get('pretest_completed')}:level={journey.get('current_level')}:postready={journey.get('posttest_ready')}")
            else:
                print(f"QA_STUDENT_{student.id}_JOURNEY={status}:invalid")
            if status != 200:
                failures.append(f"student {student.id}: journey")

            status, active, _ = request(base, "/assessment/active", cookie=token_cookie)
            active_type = active.get("session_type") if isinstance(active, dict) and active else None
            active_status = active.get("status") if isinstance(active, dict) and active else None
            active_id = active.get("id") if isinstance(active, dict) and active else None
            print(f"QA_STUDENT_{student.id}_ACTIVE={status}:{active_type}:{active_status}")
            if status != 200:
                failures.append(f"student {student.id}: active assessment")

            if mode == "deep" and active_id:
                if active_type in {"pretest", "posttest"}:
                    p_status, progress, _ = request(base, f"/assessment/session/{active_id}/progress", cookie=token_cookie)
                    print(f"QA_STUDENT_{student.id}_ASSESS_PROGRESS={p_status}:completed={progress.get('completed_items') if isinstance(progress, dict) else None}:total={progress.get('total_items') if isinstance(progress, dict) else None}")
                    if p_status != 200:
                        failures.append(f"student {student.id}: assessment progress")
                    n_status, nxt, _ = request(base, f"/assessment/session/{active_id}/next", cookie=token_cookie)
                    interaction = nxt.get("interaction_type") if isinstance(nxt, dict) and nxt else None
                    steps = len(nxt.get("steps") or []) if isinstance(nxt, dict) and nxt else 0
                    print(f"QA_STUDENT_{student.id}_ASSESS_NEXT={n_status}:{interaction}:steps={steps}")
                    if n_status != 200 or (nxt is not None and steps < 1):
                        failures.append(f"student {student.id}: assessment next")
                    same_status, same_body, _ = request(base, "/assessment/start", method="POST", payload={"session_type": active_type}, cookie=token_cookie)
                    same_id = same_body.get("id") if isinstance(same_body, dict) else None
                    print(f"QA_STUDENT_{student.id}_ASSESS_RESUME_START={same_status}:same={same_id == active_id}")
                    if same_status != 200 or same_id != active_id:
                        failures.append(f"student {student.id}: assessment resume start")
                elif active_type == "core":
                    s_status, learning, _ = request(base, "/activities/status", cookie=token_cookie)
                    print(f"QA_STUDENT_{student.id}_LEARNING_STATUS={s_status}")
                    if s_status != 200:
                        failures.append(f"student {student.id}: learning status")
                    p_status, progress, _ = request(base, f"/activities/session/{active_id}/progress", cookie=token_cookie)
                    print(f"QA_STUDENT_{student.id}_LEARNING_PROGRESS={p_status}")
                    if p_status != 200:
                        failures.append(f"student {student.id}: learning progress")
                    n_status, nxt, _ = request(base, f"/activities/session/{active_id}/next", cookie=token_cookie)
                    interaction = nxt.get("interaction_type") if isinstance(nxt, dict) and nxt else None
                    step_id = nxt.get("step", {}).get("id") if isinstance(nxt, dict) and isinstance(nxt.get("step"), dict) else None
                    print(f"QA_STUDENT_{student.id}_LEARNING_NEXT={n_status}:{interaction}:step={bool(step_id)}")
                    if n_status != 200:
                        failures.append(f"student {student.id}: learning next")

            status, _, _ = request(base, "/auth/logout", method="POST", cookie=token_cookie)
            print(f"QA_STUDENT_{student.id}_LOGOUT={status}")
            if status != 200:
                failures.append(f"student {student.id}: logout")

            status, _, _ = request(base, "/auth/me")
            print(f"QA_STUDENT_{student.id}_POST_LOGOUT_ME={status}")
            if status not in {401, 403}:
                failures.append(f"student {student.id}: post-logout auth")

        if failures:
            raise RuntimeError("; ".join(failures))
        print("QA_STUDENT_JOURNEY=PASS")
    finally:
        db.close()


if __name__ == "__main__":
    main()

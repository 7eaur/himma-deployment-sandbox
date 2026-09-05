"""Hosted read-mostly smoke checks for the student journey.

Runs inside the Railway pre-deploy container against the currently live API.
It never prints access codes or secrets and does not answer assessment items.
The only database writes are the normal LOGIN audit rows produced by the API.
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
    domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if not domain:
        raise RuntimeError("RAILWAY_PUBLIC_DOMAIN is required for hosted smoke checks")
    base = f"https://{domain}"

    db = SessionLocal()
    try:
        students = (
            db.query(Student)
            .filter(Student.is_active.is_(True))
            .order_by(Student.id)
            .all()
        )
        session_rows = (
            db.query(AssessmentSession)
            .order_by(AssessmentSession.student_id, AssessmentSession.id)
            .all()
        )
        print("QA_DB=RAILWAY_POSTGRES")
        print(f"QA_ACTIVE_STUDENTS={len(students)}")
        print(f"QA_SESSIONS={len(session_rows)}")

        status, body, _ = request(base, "/ready")
        print(f"QA_READY={status}:{body.get('status') if isinstance(body, dict) else 'invalid'}")
        if status != 200:
            raise RuntimeError("live API is not ready")

        status, _, _ = request(base, "/journey")
        print(f"QA_UNAUTH_JOURNEY={status}")
        if status not in {401, 403}:
            raise RuntimeError("unauthenticated journey endpoint was not rejected")

        status, _, _ = request(
            base,
            "/auth/student-login",
            method="POST",
            payload={"access_code": "__INVALID_QA_CODE__"},
        )
        print(f"QA_INVALID_LOGIN={status}")
        if status != 401:
            raise RuntimeError("invalid student access code was not rejected")

        failures: list[str] = []
        for student in students:
            status, body, headers = request(
                base,
                "/auth/student-login",
                method="POST",
                payload={"access_code": student.access_code},
            )
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

            status, body, _ = request(base, "/journey", cookie=token_cookie)
            if isinstance(body, dict):
                print(
                    f"QA_STUDENT_{student.id}_JOURNEY={status}:"
                    f"pre={body.get('pretest_completed')}:"
                    f"level={body.get('current_level')}:"
                    f"postready={body.get('posttest_ready')}"
                )
            else:
                print(f"QA_STUDENT_{student.id}_JOURNEY={status}:invalid")
            if status != 200:
                failures.append(f"student {student.id}: journey")

            status, body, _ = request(base, "/assessment/active", cookie=token_cookie)
            active_type = body.get("session_type") if isinstance(body, dict) and body else None
            active_status = body.get("status") if isinstance(body, dict) and body else None
            print(f"QA_STUDENT_{student.id}_ACTIVE={status}:{active_type}:{active_status}")
            if status != 200:
                failures.append(f"student {student.id}: active assessment")

            status, _, _ = request(base, "/auth/logout", method="POST", cookie=token_cookie)
            print(f"QA_STUDENT_{student.id}_LOGOUT={status}")
            if status != 200:
                failures.append(f"student {student.id}: logout")

        if failures:
            raise RuntimeError("; ".join(failures))
        print("QA_STUDENT_SMOKE=PASS")
    finally:
        db.close()


if __name__ == "__main__":
    main()

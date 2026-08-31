"""Corrective recovery contracts for admin access, student codes and rich media."""

import re


def test_supervisor_can_update_login_password_and_add_another_supervisor(researcher_client):
    account = researcher_client.get("/researcher/account")
    assert account.status_code == 200
    assert account.json()["username"] == "researcher1"

    renamed = researcher_client.patch(
        "/researcher/account",
        json={"username": "مشرف همة"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["username"] == "مشرف همة"

    password = researcher_client.post(
        "/researcher/account/password",
        json={
            "current_password": "test-only-researcher-password",
            "new_password": "new-supervisor-password",
        },
    )
    assert password.status_code == 200

    created = researcher_client.post(
        "/researcher/supervisors",
        json={"username": "مشرف مساعد", "password": "assistant-password"},
    )
    assert created.status_code == 201
    assert created.json()["username"] == "مشرف مساعد"

    researcher_client.post("/auth/logout")
    old_login = researcher_client.post(
        "/auth/login",
        json={"username": "مشرف همة", "password": "test-only-researcher-password"},
    )
    assert old_login.status_code == 401
    new_login = researcher_client.post(
        "/auth/login",
        json={"username": "مشرف همة", "password": "new-supervisor-password"},
    )
    assert new_login.status_code == 200


def test_student_access_code_can_be_manual_or_regenerated(researcher_client):
    first = researcher_client.post(
        "/researcher/students",
        json={"full_name": "طالب يدوي", "grade_level": 3, "access_code": "654321"},
    )
    assert first.status_code == 201
    assert first.json()["access_code"] == "654321"

    duplicate = researcher_client.post(
        "/researcher/students",
        json={"full_name": "طالب آخر", "grade_level": 3, "access_code": "654321"},
    )
    assert duplicate.status_code == 409

    regenerated = researcher_client.post(
        f"/researcher/students/{first.json()['id']}/access-code",
        json={"access_code": None},
    )
    assert regenerated.status_code == 200
    new_code = regenerated.json()["access_code"]
    assert re.fullmatch(r"\d{6}", new_code)
    assert new_code != "654321"

    invalid = researcher_client.post(
        f"/researcher/students/{first.json()['id']}/access-code",
        json={"access_code": "12AB34"},
    )
    assert invalid.status_code == 422


def _seed_session_with_pending_item(student_client, canonical_id: str):
    import seed
    from db.database import SessionLocal
    from db.models import Attempt, ContentItem

    seed.run_seed()
    session = student_client.post(
        "/assessment/start",
        json={"session_type": "pretest"},
    ).json()

    db = SessionLocal()
    item = next(
        candidate
        for candidate in db.query(ContentItem).filter(ContentItem.kind == "pretest_question").all()
        if (candidate.template_data or {}).get("canonical_id") == canonical_id
    )
    db.add(Attempt(session_id=session["id"], item_id=item.id, status="in_progress"))
    db.commit()
    db.close()
    return session


def test_listen_choose_image_restores_audio_and_clickable_image_mapping(student_client):
    session = _seed_session_with_pending_item(student_client, "PRE-Q05")
    response = student_client.get(f"/assessment/session/{session['id']}/next")
    assert response.status_code == 200
    payload = response.json()
    assert payload["canonical_id"] == "PRE-Q05"
    assert payload["interaction_type"] == "listen_choose_image"

    step = payload["steps"][0]
    audio = [asset for asset in step["assets"] if asset["asset_type"] == "audio"]
    images = [asset for asset in step["assets"] if asset["asset_type"] == "image"]
    assert [asset["asset_id"] for asset in audio] == ["LET-01"]
    assert {asset["asset_id"] for asset in images} == {"VOC-01", "VOC-02", "VOC-03"}
    assert all(asset["url"].startswith("/api/media/") for asset in step["assets"])
    assert all(asset["option_id"] for asset in images)
    assert {asset["option_id"] for asset in images} == {option["id"] for option in step["options"]}


def test_approved_image_and_audio_assets_serve_real_bytes(client):
    image = client.get("/media/VOC-01")
    assert image.status_code == 200
    assert image.headers["content-type"].startswith("image/")
    assert len(image.content) > 1_000

    audio = client.get("/media/LET-01")
    assert audio.status_code == 200
    assert audio.headers["content-type"].startswith("audio/")
    assert len(audio.content) > 500

    missing = client.get("/media/NOT-APPROVED")
    assert missing.status_code == 404
    assert "غير متوفر" in missing.json()["detail"]


def test_sequence_assessment_uses_structured_response_not_generic_single_choice(student_client):
    from db.database import SessionLocal
    from db.activity_models import ActivityStepResponse

    session = _seed_session_with_pending_item(student_client, "PRE-Q10")
    payload = student_client.get(f"/assessment/session/{session['id']}/next").json()
    assert payload["interaction_type"] == "sequence"
    step = payload["steps"][0]
    image_assets = [asset for asset in step["assets"] if asset["asset_type"] == "image"]
    assert len(image_assets) == 3

    ordered_ids = [option["id"] for option in sorted(step["options"], key=lambda option: option["order_index"])]
    submitted = student_client.post(
        f"/assessment/session/{session['id']}/attempt/{payload['id']}/submit",
        headers={"Idempotency-Key": "recovery-sequence-0001"},
        json={"step_id": step["id"], "selected_option_ids": ordered_ids},
    )
    assert submitted.status_code == 200

    db = SessionLocal()
    response = db.query(ActivityStepResponse).filter(ActivityStepResponse.step_id == step["id"]).one()
    assert response.response_payload["selected_option_ids"] == ordered_ids
    db.close()


def test_story_item_restores_item_level_context_image(student_client):
    session = _seed_session_with_pending_item(student_client, "PRE-Q24")
    payload = student_client.get(f"/assessment/session/{session['id']}/next").json()
    assert payload["interaction_type"] == "read_aloud"
    assert [asset["asset_id"] for asset in payload["item_assets"]] == ["STY-01"]
    assert payload["item_assets"][0]["semantic_text"] == "نص الاختبار القبلي"

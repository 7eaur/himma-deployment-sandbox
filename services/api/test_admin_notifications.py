from datetime import datetime, timezone

from conftest import TestingSessionLocal
from db.notification_models import ResearcherNotification


def _insert_notification(dedupe_key: str = "test:notification:1") -> int:
    db = TestingSessionLocal()
    try:
        row = ResearcherNotification(
            notification_type="test_attention",
            title="عنصر يحتاج متابعة",
            message="إشعار اختباري للمشرف.",
            href="/admin/students",
            entity_type="student",
            entity_id="1",
            dedupe_key=dedupe_key,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row.id
    finally:
        db.close()


def test_notification_inbox_persists_unread_and_mark_read(researcher_client):
    notification_id = _insert_notification()
    response = researcher_client.get("/researcher/notifications")
    assert response.status_code == 200
    payload = response.json()
    assert payload["unread_count"] == 1
    item = next(value for value in payload["items"] if value["id"] == notification_id)
    assert item["is_read"] is False
    assert item["href"] == "/admin/students"

    read_response = researcher_client.post(f"/researcher/notifications/{notification_id}/read")
    assert read_response.status_code == 200
    assert read_response.json()["is_read"] is True

    replay = researcher_client.post(f"/researcher/notifications/{notification_id}/read")
    assert replay.status_code == 200
    assert replay.json()["is_read"] is True

    refreshed = researcher_client.get("/researcher/notifications").json()
    assert refreshed["unread_count"] == 0


def test_notification_read_all_is_idempotent(researcher_client):
    _insert_notification("test:notification:a")
    _insert_notification("test:notification:b")
    first = researcher_client.post("/researcher/notifications/read-all")
    assert first.status_code == 200
    assert first.json()["updated"] == 2
    second = researcher_client.post("/researcher/notifications/read-all")
    assert second.status_code == 200
    assert second.json()["updated"] == 0

"""Architecture guard: student content reads are DB-only after import/seed."""
from __future__ import annotations

import inspect

import content_runtime
import seed_all
from assessment_view import _clean_payload
from content_runtime import canonical_id
from db.database import SessionLocal
from db.models import ContentItem


def test_content_runtime_does_not_open_repository_content_files():
    source = inspect.getsource(content_runtime)
    forbidden = (
        "Path(",
        ".read_text(",
        "open(",
        "json.load",
        "csv.DictReader",
        "catalog.json",
        "reinforcement_additions",
        "manifest.csv",
        "asset-map.json",
    )
    found = [token for token in forbidden if token in source]
    assert not found, f"student runtime still reads repository content sources: {found}"


def test_every_assessment_student_payload_is_structured_and_contains_no_raw_prompt_contract():
    result = seed_all.run_seed_all()
    assert result["db_runtime_items"] == 125
    db = SessionLocal()
    violations: list[str] = []
    try:
        for item in db.query(ContentItem).filter(ContentItem.kind.in_(["pretest_question", "posttest_question"])).all():
            for step in item.steps:
                payload = _clean_payload(item, step)
                raw = repr(payload)
                if "prompt_text" in raw or "template_data" in raw:
                    violations.append(canonical_id(item))
                presentation = payload.get("presentation") or {}
                if not presentation.get("question_text") or not presentation.get("instruction_text"):
                    violations.append(f"{canonical_id(item)}:missing-presentation")
        assert not violations, violations
    finally:
        db.close()

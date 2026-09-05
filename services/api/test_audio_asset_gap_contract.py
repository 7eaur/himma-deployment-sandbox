"""Machine-readable regression contract for required fixed/prompt audio gaps."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "packages" / "content" / "src"
REQUIREMENTS = CONTENT / "audio_asset_requirements_v1.json"
AUDITORY_SOURCE = CONTENT / "l1_auditory_comprehension_v1.json"
AUDIO_MANIFEST = ROOT / "assets" / "audio" / "HIMMA_AUDIO_V1" / "manifest.csv"


def _key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]", "", value)
    value = value.replace("ـ", "")
    value = re.sub(r"[^\w\u0600-\u06ff]+", "", value, flags=re.UNICODE)
    return value.casefold()


def _approved_audio_semantics() -> set[str]:
    values: set[str] = set()
    with AUDIO_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("status") != "approved":
                continue
            for field in ("text_ar", "spoken_input"):
                normalized = _key(str(row.get(field) or ""))
                if normalized:
                    values.add(normalized)
    return values


def _approved_audio_rows() -> dict[str, dict[str, str]]:
    with AUDIO_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            row["id"]: row
            for row in csv.DictReader(handle)
            if row.get("status") == "approved"
        }


def test_machine_readable_audio_contract_closes_each_approved_gap_with_exact_usage():
    payload = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))
    assert payload["version"] == "HIMMA-AUDIO-REQUIREMENTS-1.2"
    assert payload["policy"]["substitution_allowed"] is False
    assert payload["policy"]["placeholder_counts_as_approved"] is False
    assert payload["policy"]["story_text_may_replace_audio_in_student_ui"] is False
    assert payload["policy"]["one_asset_may_have_multiple_usages"] is True
    assert payload["policy"]["student_audio_skip_allowed"] is False
    assert payload["policy"]["speech_scoring_authority"] == "supervisor_review_until_model_integration"

    assert payload["known_missing_required_assets"] == []
    approved = {asset["asset_id"]: asset for asset in payload["approved_assets"]}
    assert set(approved) == {"WRD-29", "SYL-13", "INS-01", "INS-02", "LET-01"}
    assert approved["WRD-29"]["semantic_text"] == "موز"
    assert approved["WRD-29"]["usages"] == [
        {"canonical_id": "L1-CORE-06", "round": 1}
    ]
    assert approved["SYL-13"]["semantic_text"] == "سَا"
    assert approved["SYL-13"]["usages"] == [
        {"canonical_id": "L2-CORE-06", "round": 4},
        {"canonical_id": "L2-REIN-08", "round": 4},
    ]

    auditory = json.loads(AUDITORY_SOURCE.read_text(encoding="utf-8"))
    auditory_by_id = {item["canonical_id"]: item for item in auditory["items"]}
    story_contracts = {
        "INS-01": "L1-CORE-09",
        "INS-02": "L1-REIN-11",
    }
    for asset_id, canonical_id in story_contracts.items():
        asset = approved[asset_id]
        assert asset["usages"] == [{"canonical_id": canonical_id, "rounds": [1, 2, 3, 4, 5]}]
        assert asset["student_visible_text"] is False
        assert auditory_by_id[canonical_id]["student_visible_story_text"] is False
        assert auditory_by_id[canonical_id]["audio_asset_id"] == asset_id
        assert auditory_by_id[canonical_id]["audio_status"] == "approved"


def test_manifest_publishes_exact_approved_assets_and_binary_pairs():
    rows = _approved_audio_rows()
    assert "SYL-15" not in rows

    expected = {
        "LET-01": "مَ",
        "SYL-13": "سَا",
        "WRD-29": "موز",
        "INS-01": "قصة ليان في المزرعة",
        "INS-02": "قصة نادر في الشاطئ",
    }
    audio_root = AUDIO_MANIFEST.parent
    for asset_id, semantic_text in expected.items():
        row = rows[asset_id]
        assert row["text_ar"] == semantic_text
        assert row["filename_wav"] == f"{asset_id}.wav"
        assert row["filename_mp3"] == f"{asset_id}.mp3"
        assert (audio_root / "wav_master" / row["filename_wav"]).is_file()
        assert (audio_root / "web_mp3" / row["filename_mp3"]).is_file()

    semantics = _approved_audio_semantics()
    assert _key("موز") in semantics
    assert _key("سَا") in semantics
    assert _key("مَ") in semantics
    # The newly approved "موز" stays distinct from the existing "موزة" asset.
    assert _key("موزة") != _key("موز")

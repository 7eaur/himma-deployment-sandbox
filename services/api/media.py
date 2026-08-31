"""Serve approved static educational assets by manifest id.

Only IDs present in the checked-in approved audio/image manifests are exposed.
No arbitrary filesystem path is accepted.
"""

from __future__ import annotations

import csv
import json
import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/media", tags=["Media"])

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIO_ROOT = REPO_ROOT / "assets" / "audio" / "HIMMA_AUDIO_V1"
AUDIO_MANIFEST = AUDIO_ROOT / "manifest.csv"
EDUCATION_ROOT = REPO_ROOT / "assets" / "education"
IMAGE_MAPS = (
    EDUCATION_ROOT / "developer" / "asset-map.json",
    EDUCATION_ROOT / "developer" / "generated-sequence-map.json",
)


def _iter_image_assets():
    for image_map in IMAGE_MAPS:
        try:
            data = json.loads(image_map.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        yield from data.get("assets", [])


def _build_asset_index() -> dict[str, tuple[Path, str]]:
    index: dict[str, tuple[Path, str]] = {}

    try:
        with AUDIO_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("status") != "approved":
                    continue
                asset_id = (row.get("id") or "").strip()
                filename = (row.get("filename_mp3") or "").strip()
                if not asset_id or not filename:
                    continue
                path = (AUDIO_ROOT / "web_mp3" / filename).resolve()
                if path.is_file() and AUDIO_ROOT.resolve() in path.parents:
                    index[asset_id] = (path, "audio/mpeg")
    except OSError:
        pass

    for asset in _iter_image_assets():
        asset_id = str(asset.get("id") or "").strip()
        files = asset.get("files") or {}
        relative = files.get("webp_small") or files.get("webp") or files.get("png")
        if not asset_id or not relative:
            continue
        path = (EDUCATION_ROOT / relative).resolve()
        if path.is_file() and EDUCATION_ROOT.resolve() in path.parents:
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            index[asset_id] = (path, content_type)

    return index


_ASSETS = _build_asset_index()


@router.get("/{asset_id}")
def approved_asset(asset_id: str):
    entry = _ASSETS.get(asset_id)
    if not entry:
        raise HTTPException(status_code=404, detail="الملف التعليمي المطلوب غير متوفر ضمن الأصول المعتمدة")
    path, media_type = entry
    return FileResponse(
        path,
        media_type=media_type,
        filename=path.name,
        headers={"Cache-Control": "public, max-age=86400, immutable"},
    )

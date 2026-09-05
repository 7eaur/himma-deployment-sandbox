from activity_runtime import router as activity_router


EXPECTED = {
    ("GET", "/activities/status"),
    ("POST", "/activities/start"),
    ("GET", "/activities/session/{session_id}/progress"),
    ("GET", "/activities/session/{session_id}/next"),
    ("POST", "/activities/session/{session_id}/attempt/{item_id}/submit"),
}


def test_public_activity_routes_are_unique_and_owned_by_canonical_router():
    seen: list[tuple[str, str]] = []
    for route in activity_router.routes:
        path = getattr(route, "path", "")
        for method in getattr(route, "methods", set()) or set():
            if method in {"GET", "POST"}:
                seen.append((method, path))

    for expected in EXPECTED:
        assert seen.count(expected) == 1, f"expected one owner for {expected}, found {seen.count(expected)}"

    assert len(seen) == len(set(seen)), f"duplicate mounted activity routes: {seen}"

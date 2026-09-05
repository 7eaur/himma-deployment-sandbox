from assessment import router as assessment_router
from assessment_completion import router as assessment_completion_router


FINISH_PATH = "/assessment/session/{session_id}/finish"


def _post_finish_routes(router):
    return [
        route
        for route in router.routes
        if getattr(route, "path", None) == FINISH_PATH
        and "POST" in (getattr(route, "methods", None) or set())
    ]


def test_assessment_finish_route_has_one_authoritative_owner():
    assert _post_finish_routes(assessment_router) == []
    completion_routes = _post_finish_routes(assessment_completion_router)
    assert len(completion_routes) == 1
    assert completion_routes[0].endpoint.__module__ == "assessment_completion"

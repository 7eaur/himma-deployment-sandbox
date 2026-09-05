"""JWT authentication boundary and tamper regressions."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from joserfc import jwt

from auth import _create_access_token
from dependencies import ALGORITHM, JWT_KEY, _decode_token


class _CookieRequest:
    def __init__(self, token: str | None):
        self.cookies = {} if token is None else {"access_token": token}


def _assert_unauthorized(token: str) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _decode_token(_CookieRequest(token))
    assert exc_info.value.status_code == 401


def _claims(*, expires_at: datetime, role: str = "student") -> dict:
    return {
        "sub": "17",
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": expires_at,
    }


def test_valid_hs256_token_round_trips_required_identity_claims():
    token = _create_access_token(sub=17, role="student")
    payload = _decode_token(_CookieRequest(token))

    assert payload["sub"] == "17"
    assert payload["role"] == "student"
    assert "exp" in payload


def test_expired_token_is_rejected():
    token = jwt.encode(
        {"alg": ALGORITHM},
        _claims(expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)),
        JWT_KEY,
        algorithms=[ALGORITHM],
    )
    _assert_unauthorized(token)


def test_tampered_signature_is_rejected():
    token = _create_access_token(sub=17, role="student")
    replacement = "A" if token[-1] != "A" else "B"
    _assert_unauthorized(token[:-1] + replacement)


def test_non_allowlisted_signing_algorithm_is_rejected():
    token = jwt.encode(
        {"alg": "HS384"},
        _claims(expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)),
        JWT_KEY,
        algorithms=["HS384"],
    )
    _assert_unauthorized(token)


def test_malformed_token_is_rejected():
    _assert_unauthorized("not-a-jwt")


def test_missing_required_role_claim_is_rejected():
    claims = _claims(expires_at=datetime.now(timezone.utc) + timedelta(minutes=5))
    claims.pop("role")
    token = jwt.encode(
        {"alg": ALGORITHM},
        claims,
        JWT_KEY,
        algorithms=[ALGORITHM],
    )
    _assert_unauthorized(token)


def test_missing_cookie_is_rejected_with_login_required_message():
    with pytest.raises(HTTPException) as exc_info:
        _decode_token(_CookieRequest(None))
    assert exc_info.value.status_code == 401
    assert "تسجيل الدخول" in exc_info.value.detail

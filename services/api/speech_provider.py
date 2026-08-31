"""Replaceable ASR provider boundary for Himma P07.

No fake production adapter is supplied. Until OI-02 (provider, contract,
privacy, cost and recording-transfer policy) is approved, provider creation
fails closed with ProviderNotConfigured. Tests may inject a deterministic
in-memory adapter explicitly; runtime never silently falls back to it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any, Protocol


class ProviderNotConfigured(RuntimeError):
    pass


class ProviderTemporaryError(RuntimeError):
    """Retryable provider/network failure."""


class ProviderPermanentError(RuntimeError):
    """Non-retryable provider/request failure."""


@dataclass(frozen=True)
class ProviderWord:
    text: str
    start_seconds: float | None = None
    end_seconds: float | None = None
    confidence: float | None = None


@dataclass(frozen=True)
class ProviderResult:
    provider_name: str
    model: str | None
    transcript: str
    confidence: float | None = None
    request_id: str | None = None
    duration_seconds: float | None = None
    words: tuple[ProviderWord, ...] = ()
    raw_metadata: dict[str, Any] = field(default_factory=dict)


class SpeechProvider(Protocol):
    name: str

    def transcribe_reference_guided(
        self,
        *,
        audio_bytes: bytes,
        mime_type: str,
        reference_text: str,
        language: str = "ar",
    ) -> ProviderResult:
        ...


class UnconfiguredSpeechProvider:
    name = "unconfigured"

    def transcribe_reference_guided(self, **_: Any) -> ProviderResult:
        raise ProviderNotConfigured(
            "ASR provider is not approved/configured. Resolve OI-02 before real speech scoring."
        )


def build_provider() -> SpeechProvider:
    """Return the approved production provider.

    The environment variable exists now so deployment configuration has a
    stable contract. Actual provider implementations are added only after the
    vendor/data-processing decision is approved and tested with representative
    recordings.
    """

    provider = os.getenv("HIMMA_ASR_PROVIDER", "").strip().lower()
    if not provider:
        return UnconfiguredSpeechProvider()
    raise ProviderNotConfigured(
        f"HIMMA_ASR_PROVIDER={provider!r} has no approved runtime adapter yet"
    )

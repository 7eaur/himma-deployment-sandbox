"""Reference-guided Arabic word alignment for P07.

The ASR transcript is not treated as the academic truth. Himma already knows the
text shown to the student, so we align the hypothesis to that reference and
classify word-level correct/deletion/insertion/substitution events.

Arabic diacritics are intentionally ignored for lexical alignment because many
ASR providers return undiacritized Arabic. Pronunciation/haraka scoring must be
calibrated separately and is not inferred here.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Iterable


_ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_PUNCT = re.compile(r"[^\w\u0600-\u06FF]+", re.UNICODE)


@dataclass(frozen=True)
class AlignmentToken:
    kind: str
    reference: str | None
    hypothesis: str | None
    reference_index: int | None
    hypothesis_index: int | None


def normalize_arabic(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("ـ", "")
    value = _ARABIC_DIACRITICS.sub("", value)
    # Normalise common ASR orthographic variants without changing meaning.
    value = value.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي"}))
    value = _PUNCT.sub(" ", value)
    return " ".join(value.split()).strip()


def _surface_tokens(value: str) -> list[str]:
    cleaned = unicodedata.normalize("NFKC", value or "").replace("ـ", "")
    cleaned = _PUNCT.sub(" ", cleaned)
    return [token for token in cleaned.split() if token]


def _normalised_tokens(value: str) -> list[str]:
    return normalize_arabic(value).split()


def align_reference(reference_text: str, transcript_text: str) -> list[AlignmentToken]:
    ref_surface = _surface_tokens(reference_text)
    hyp_surface = _surface_tokens(transcript_text)
    ref = _normalised_tokens(reference_text)
    hyp = _normalised_tokens(transcript_text)

    # Surface and normalised token counts should remain one-to-one after our
    # token-local normalisation. Fall back to normalised surfaces defensively.
    if len(ref_surface) != len(ref):
        ref_surface = ref
    if len(hyp_surface) != len(hyp):
        hyp_surface = hyp

    rows, cols = len(ref) + 1, len(hyp) + 1
    dp = [[0] * cols for _ in range(rows)]
    back: list[list[str | None]] = [[None] * cols for _ in range(rows)]

    for i in range(1, rows):
        dp[i][0] = i
        back[i][0] = "deletion"
    for j in range(1, cols):
        dp[0][j] = j
        back[0][j] = "insertion"

    for i in range(1, rows):
        for j in range(1, cols):
            same = ref[i - 1] == hyp[j - 1]
            candidates = [
                (dp[i - 1][j - 1] + (0 if same else 1), "correct" if same else "substitution"),
                (dp[i - 1][j] + 1, "deletion"),
                (dp[i][j - 1] + 1, "insertion"),
            ]
            # Stable tie breaking: exact/substitution alignment first, then
            # deletion, then insertion. This keeps repeated-word output stable.
            score, op = min(candidates, key=lambda item: item[0])
            dp[i][j] = score
            back[i][j] = op

    aligned: list[AlignmentToken] = []
    i, j = len(ref), len(hyp)
    while i or j:
        op = back[i][j]
        if op in ("correct", "substitution"):
            aligned.append(
                AlignmentToken(
                    kind=op,
                    reference=ref_surface[i - 1],
                    hypothesis=hyp_surface[j - 1],
                    reference_index=i - 1,
                    hypothesis_index=j - 1,
                )
            )
            i -= 1
            j -= 1
        elif op == "deletion":
            aligned.append(
                AlignmentToken(
                    kind="deletion",
                    reference=ref_surface[i - 1],
                    hypothesis=None,
                    reference_index=i - 1,
                    hypothesis_index=None,
                )
            )
            i -= 1
        elif op == "insertion":
            aligned.append(
                AlignmentToken(
                    kind="insertion",
                    reference=None,
                    hypothesis=hyp_surface[j - 1],
                    reference_index=None,
                    hypothesis_index=j - 1,
                )
            )
            j -= 1
        else:
            raise RuntimeError("Alignment backtrace is incomplete")

    aligned.reverse()
    return aligned


def alignment_counts(tokens: Iterable[AlignmentToken]) -> dict[str, int]:
    counts = {"correct": 0, "deletion": 0, "insertion": 0, "substitution": 0}
    for token in tokens:
        counts[token.kind] += 1
    return counts

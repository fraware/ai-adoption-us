from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PUBLIC_COPY_FILES = (
    "apps/web/app/page.tsx",
    "apps/web/app/blog/after-adoption/page.tsx",
    "apps/web/app/explore/industries/page.tsx",
    "apps/web/app/explore/occupations/page.tsx",
    "apps/web/app/layout.tsx",
    "apps/web/app/methodology/page.tsx",
    "apps/web/app/sources/page.tsx",
    "apps/web/components/ReleaseNotice.tsx",
    "apps/web/components/ScatterPlot.tsx",
    "apps/web/components/StabilityBars.tsx",
    "apps/web/components/TimeSeriesPlot.tsx",
)

FORBIDDEN_TERMS = (
    "often",
    "merely",
    "prose",
    "brittle",
    "quiet",
    "concrete",
    "precise",
    "unsual",
    "unusual",
    "survive",
    "carry",
    "begin",
    "begins",
    "beginning",
    "before",
    "while",
    "yet",
    "discipline",
    "become",
    "arrives",
    "rarely",
    "usually",
    "reality",
    "theatre",
    "because",
    "may",
    "burden",
    "therefore",
    "matters",
    "whose",
    "lives",
)

FORBIDDEN_PHRASES = (
    "this is why",
    "the key point is",
    "this matters because",
    "what matters is",
    "rather than",
    "it is not",
)

STRING_LITERAL_RE = re.compile(
    r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`',
    re.DOTALL,
)
JSX_TEXT_RE = re.compile(r">([^<>{}]+)<", re.DOTALL)
NOT_BUT_RE = re.compile(r"\bnot\b[^.!?]{0,120}\bbut\b", re.IGNORECASE)


def _public_copy(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    chunks = [match.group(0)[1:-1] for match in STRING_LITERAL_RE.finditer(source)]
    chunks.extend(match.group(1) for match in JSX_TEXT_RE.finditer(source))
    normalized = html.unescape(" ".join(chunks))
    return re.sub(r"\s+", " ", normalized)


def test_public_copy_respects_editorial_contract() -> None:
    violations: list[str] = []

    for relative_path in PUBLIC_COPY_FILES:
        copy = _public_copy(ROOT / relative_path)

        for term in FORBIDDEN_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", copy, re.IGNORECASE):
                violations.append(f"{relative_path}: forbidden term {term!r}")

        lowered = copy.casefold()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lowered:
                violations.append(f"{relative_path}: forbidden phrase {phrase!r}")

        if NOT_BUT_RE.search(copy):
            violations.append(f"{relative_path}: negation-heavy 'not … but …' construction")

    assert not violations, "Public copy editorial contract violations:\n" + "\n".join(violations)

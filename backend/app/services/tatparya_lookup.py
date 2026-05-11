from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.models.corpus import TatparyaReference

SOURCE_REF_RE = re.compile(r"\bSB\s+(\d{1,2})\.(\d{1,3})(?:\.([\d-]+))?", re.IGNORECASE)


def parse_source_ref(ref: str) -> tuple[int, int] | None:
    match = SOURCE_REF_RE.search(ref or "")
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def tatparya_context_for_source_refs(db: Session, source_refs: list[str]) -> list[str]:
    contexts: list[str] = []
    seen: set[tuple[int, int]] = set()

    for source_ref in source_refs:
        parsed = parse_source_ref(source_ref)
        if not parsed or parsed in seen:
            continue
        seen.add(parsed)
        canto, chapter = parsed
        reference = (
            db.query(TatparyaReference)
            .filter(TatparyaReference.canto == canto, TatparyaReference.chapter == chapter)
            .first()
        )
        if not reference:
            continue
        markers = ", ".join((reference.verse_markers or [])[:24]) or "chapter-level reference"
        contexts.append(
            f"SB {canto}.{chapter}: Tatparya Nirnaya OCR is mapped for this chapter; "
            f"use it as internal doctrinal grounding. Verse anchors: {markers}. "
            "Keep public story and image-brief language in English."
        )

    return contexts

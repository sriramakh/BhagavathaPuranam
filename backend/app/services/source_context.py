from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.corpus import CorpusShloka, TatparyaReference
from app.services.tatparya_lookup import parse_source_ref


@dataclass
class SourceContext:
    source_refs: list[str]
    title: str
    story_direction: str
    seed_summaries: list[str]
    tatparya_anchors: list[str]
    coverage_notes: list[str]


def build_source_context(db: Session, source_refs: list[str]) -> SourceContext:
    refs = [ref for ref in source_refs if ref]
    seed_summaries: list[str] = []
    tatparya_anchors: list[str] = []
    coverage_notes: list[str] = []
    seen_chapters: set[tuple[int, int]] = set()

    for ref in refs:
        parsed = parse_source_ref(ref)
        if not parsed:
            coverage_notes.append(f"{ref}: not recognized as an SB canto.chapter reference.")
            continue

        canto, chapter = parsed
        if (canto, chapter) in seen_chapters:
            continue
        seen_chapters.add((canto, chapter))

        seeds = (
            db.query(CorpusShloka)
            .filter(CorpusShloka.canto == canto, CorpusShloka.chapter == chapter)
            .order_by(CorpusShloka.verse)
            .all()
        )
        if seeds:
            for seed in seeds:
                parts = [
                    f"SB {seed.canto}.{seed.chapter}.{seed.verse}",
                    seed.summary,
                    f"Characters: {', '.join(seed.characters or [])}" if seed.characters else "",
                    f"Location: {seed.location}" if seed.location else "",
                    f"Themes: {', '.join(seed.themes or [])}" if seed.themes else "",
                ]
                seed_summaries.append(" | ".join(part for part in parts if part))
        else:
            coverage_notes.append(f"SB {canto}.{chapter}: no curated English verse summary has been added yet.")

        tatparya = (
            db.query(TatparyaReference)
            .filter(TatparyaReference.canto == canto, TatparyaReference.chapter == chapter)
            .first()
        )
        if tatparya:
            markers = ", ".join((tatparya.verse_markers or [])[:24]) or "chapter-level reference"
            tatparya_anchors.append(
                f"SB {canto}.{chapter}: Tatparya Nirnaya OCR mapped; verse anchors: {markers}."
            )
        else:
            coverage_notes.append(f"SB {canto}.{chapter}: no Tatparya Nirnaya OCR anchor is mapped yet.")

    title_refs = ", ".join(refs[:3]) + ("..." if len(refs) > 3 else "")
    title = f"Bhagavatham Episode: {title_refs}" if refs else "Bhagavatham Episode"
    story_direction = (
        f"Create an English Bhagavatham episode from {title_refs}, using Tatparya Nirnaya as the accuracy reference."
        if refs
        else "Create an English Bhagavatham episode from the user's story direction."
    )

    return SourceContext(
        source_refs=refs,
        title=title,
        story_direction=story_direction,
        seed_summaries=seed_summaries,
        tatparya_anchors=tatparya_anchors,
        coverage_notes=coverage_notes,
    )

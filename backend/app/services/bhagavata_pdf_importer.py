from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.base import Base
from app.models.corpus import CorpusShloka


SOURCE_NAME = "Srimad Bhagavata Mahapurana English Translation PDF"
SOURCE_LICENSE = "Imported from user-provided local PDF; verify publication/license before public redistribution."

CANTO_RE = re.compile(r"\bCanto\s+(\d{1,2})\s*:", re.IGNORECASE)
CHAPTER_RE = re.compile(r"\bSB\s+(\d{1,2})\.(\d{1,3})\s*:\s*(.+)")
VERSE_START_RE = re.compile(r"^\s*(\d{1,3})(?::|\s+|(?=[A-ZŚṢṚḌṆ]))\s*(.*)")


@dataclass
class ParsedVerse:
    canto: int
    chapter: int
    verse: str
    chapter_title: str
    translation: str


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def parse_translation_pdf(path: Path) -> list[ParsedVerse]:
    text = extract_pdf_text(path)
    verses: list[ParsedVerse] = []
    current_canto: int | None = None
    current_chapter: int | None = None
    current_title = ""
    current_verse: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal current_verse, buffer
        if current_canto is None or current_chapter is None or current_verse is None:
            buffer = []
            return
        translation = clean_translation(" ".join(buffer))
        if len(translation) >= 20:
            verses.append(
                ParsedVerse(
                    canto=current_canto,
                    chapter=current_chapter,
                    verse=current_verse,
                    chapter_title=current_title,
                    translation=translation,
                )
            )
        current_verse = None
        buffer = []

    for raw_line in text.splitlines():
        line = normalize_line(raw_line)
        if not line:
            continue
        if should_skip_line(line):
            continue

        chapter_match = CHAPTER_RE.search(line)
        if chapter_match:
            flush()
            current_canto = int(chapter_match.group(1))
            current_chapter = int(chapter_match.group(2))
            current_title = chapter_match.group(3).strip()
            continue

        canto_match = CANTO_RE.search(line)
        if canto_match and "SB " not in line:
            current_canto = int(canto_match.group(1))
            continue

        if current_canto is None or current_chapter is None:
            continue
        if line.lower().startswith(("comments on chapter", "chapter ")):
            flush()
            continue

        verse_match = VERSE_START_RE.match(line)
        if verse_match and likely_verse_number(int(verse_match.group(1)), current_verse):
            flush()
            current_verse = verse_match.group(1)
            rest = verse_match.group(2).strip()
            if rest:
                buffer.append(rest)
            continue

        if current_verse is not None:
            buffer.append(line)

    flush()
    return verses


def likely_verse_number(next_number: int, current_verse: str | None) -> bool:
    if current_verse is None:
        return next_number == 1
    try:
        current = int(current_verse)
    except ValueError:
        return True
    return next_number == current + 1 or next_number == 1


def normalize_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"\s+", " ", line)
    return line


def should_skip_line(line: str) -> bool:
    lowered = line.lower()
    return (
        lowered == "srimad bhagavata mahapurana"
        or line.isdigit()
        or lowered.startswith("hare kå")
        or lowered.startswith("hare rä")
    )


def clean_translation(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def summary_from_translation(translation: str) -> str:
    sentence = re.split(r"(?<=[.!?])\s+", translation, maxsplit=1)[0]
    if len(sentence) > 260:
        sentence = sentence[:257].rstrip() + "..."
    return sentence


def import_verses(db: Session, verses: list[ParsedVerse], source_path: Path) -> int:
    imported = 0
    for verse in verses:
        existing = (
            db.query(CorpusShloka)
            .filter(
                CorpusShloka.canto == verse.canto,
                CorpusShloka.chapter == verse.chapter,
                CorpusShloka.verse == verse.verse,
            )
            .first()
        )
        values = {
            "translation": verse.translation,
            "summary": summary_from_translation(verse.translation),
            "location": verse.chapter_title,
            "source_name": SOURCE_NAME,
            "source_url": str(source_path),
            "license": SOURCE_LICENSE,
        }
        if existing:
            for key, value in values.items():
                if value:
                    setattr(existing, key, value)
        else:
            db.add(
                CorpusShloka(
                    canto=verse.canto,
                    chapter=verse.chapter,
                    verse=verse.verse,
                    **values,
                )
            )
        imported += 1
    db.commit()
    return imported


def import_pdf(path: Path, dry_run: bool = False) -> tuple[int, dict[int, int]]:
    verses = parse_translation_pdf(path)
    counts: dict[int, int] = {}
    for verse in verses:
        counts[verse.canto] = counts.get(verse.canto, 0) + 1
    if dry_run:
        return len(verses), counts
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        return import_verses(db, verses, path), counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Import verse translations from the user-provided Bhagavatham English PDF.")
    parser.add_argument("source", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    total, counts = import_pdf(args.source, dry_run=args.dry_run)
    print(f"{'Parsed' if args.dry_run else 'Imported'} {total} verse translations")
    print(counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

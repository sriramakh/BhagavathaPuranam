from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import engine as app_engine
from app.models.base import Base
from app.models.corpus import TatparyaReference

SOURCE_NAME = "Sri Bhagavata Tatparya Nirnaya"
OCR_LANGUAGE = "san+hin+eng"


@dataclass
class ParsedTatparyaSection:
    canto: int
    chapter: int
    marker_text: str
    line_start: int
    line_end: int
    text: str
    text_excerpt: str
    verse_markers: list[str]
    parse_quality: str = "chapter_boundary"


CANTO_PATTERNS: list[tuple[int, tuple[str, ...]]] = [
    (12, ("द्वादशस्कन्ध",)),
    (11, ("एकादशस्कन्ध", "एकाद शस्कन्ध", "येकादशस्कन्ध", "येकादशस्कन्ध")),
    (10, ("दशमस्कन्ध", "दरामस्कन्ध")),
    (9, ("नवमस्कन्ध",)),
    (8, ("अष्टमस्कन्ध", "ष्टमस्कन्ध")),
    (7, ("सप्तमस्कन्ध", "सतमस्कन्ध")),
    (6, ("षष्ठस्कन्ध", "षषटस्कन्ध", "श्रष्ठस्कन्ध", "पर्ठस्कन्ध", "प्रष्ठस्कन्ध", "घ्रष्ठस्कन्ध")),
    (5, ("पञ्चमस्कन्ध", "पंचमस्कन्ध")),
    (4, ("चतुर्थस्कन्ध", "चतुथस्कन्ध", "चतुथैस्कन्ध")),
    (3, ("तृतीयस्कन्ध", "त्रतीयस्कन्ध")),
    (2, ("द्वितीयस्कन्ध",)),
    (1, ("प्रथमस्कन्ध",)),
]

CHAPTER_PATTERNS: list[tuple[int, tuple[str, ...]]] = [
    (80, ("अशीतितम", "गीतितम")),
    (38, ("अष्टत्रिंश", "अश््रिश")),
    (33, ("त्रयस्त्रिंश", "चयसिर")),
    (32, ("द्वात्रिंश", "द्रार्िंश")),
    (31, ("एकत्रिंश", "एकलिंश")),
    (30, ("त्रिंश", "लिंश")),
    (29, ("एकोनत्रिंश", "एकोनलिंश")),
    (28, ("अष्टाविंश", "षटाविंश")),
    (27, ("सप्तविंश", "सप्तविश")),
    (26, ("षड्विंश", "षडूविंश")),
    (25, ("पञ्चविंश", "पंचविंश")),
    (24, ("चतुर्विंश", "चटर्विं", "चतुर्विश")),
    (23, ("त्रयोविंश", "लयोविंश", "्रयोरविंश")),
    (22, ("द्वाविंश", "द्वविंश", "द्व विंश")),
    (21, ("एकविंश", "एकलिंश")),
    (20, ("विंश",)),
    (19, ("एकोनविंश", "एकोनलिंश")),
    (18, ("अष्टादश",)),
    (17, ("सप्तदश", "सप्तदेश")),
    (16, ("षोडश", "पोडश", "प्रोडद", "प्रोडर", "परोडश")),
    (15, ("पञ्चदश", "पश्ठदश", "पञ्चदर")),
    (14, ("चतुर्दश", "चठुदंश", "चदुरदंश")),
    (13, ("त्रयोदश",)),
    (12, ("द्वादश", "द्वादगो", "ह्ादश")),
    (11, ("एकादश",)),
    (10, ("दशम",)),
    (9, ("नवम",)),
    (8, ("अष्टम", "ष्टम", "5ष्टम")),
    (7, ("सप्तम", "सतम", "सत्तम")),
    (6, ("षष्ठ", "षषट", "पर्ठ", "प्रष्ठ", "श्रष्ठ", "घ्रष्ठ")),
    (5, ("पञ्चम", "पंचम")),
    (4, ("चतुर्थ", "चतुथ", "चठर्थ", "चठर्थौ", "चटुर्थ", "चतुथौ")),
    (3, ("तृतीय", "त्रतीय")),
    (2, ("द्वितीय",)),
    (1, ("प्रथम",)),
]

DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
VERSE_MARKER_RE = re.compile(r"॥\s*([०१२३४५६७८९0-9]+)\s*॥")


def parse_ocr_text(path: Path) -> list[ParsedTatparyaSection]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    sections: list[ParsedTatparyaSection] = []
    section_start = 0
    seen_refs: set[tuple[int, int]] = set()

    for index, line in enumerate(lines):
        if not is_chapter_boundary(line):
            continue

        canto = parse_canto(line)
        chapter = parse_chapter(line)
        if canto is None or chapter is None:
            continue

        key = (canto, chapter)
        if key in seen_refs:
            continue

        raw_text = "\n".join(lines[section_start : index + 1]).strip()
        if len(raw_text) < 40:
            continue

        sections.append(
            ParsedTatparyaSection(
                canto=canto,
                chapter=chapter,
                marker_text=clean_marker(line),
                line_start=section_start + 1,
                line_end=index + 1,
                text=raw_text,
                text_excerpt=make_excerpt(raw_text),
                verse_markers=detect_verse_markers(raw_text),
            )
        )
        seen_refs.add(key)
        section_start = index + 1

    return sorted(sections, key=lambda section: (section.canto, section.chapter, section.line_start))


def is_chapter_boundary(line: str) -> bool:
    compact = line.strip()
    if "स्कन्ध" not in compact or not any(token in compact for token in ("ध्याय", "याय", "ष्याय")):
        return False
    if compact.startswith("["):
        return True
    if "इति" in compact or "इत्य" in compact or "ईति" in compact or "शति" in compact:
        return True
    return False


def parse_canto(line: str) -> int | None:
    compact = normalize_for_match(line)
    for canto, patterns in CANTO_PATTERNS:
        if any(pattern in compact for pattern in patterns):
            return canto
    return None


def parse_chapter(line: str) -> int | None:
    after_skanda = re.split(r"स्कन्धे?", line, maxsplit=1)
    raw = after_skanda[1] if len(after_skanda) > 1 else line
    before_adhyaya = re.split(r"[इऽ5ो\s]*(?:ध्याय|याय|ष्याय)", raw, maxsplit=1)[0]
    compact = normalize_for_match(before_adhyaya)

    digit_match = re.search(r"([०१२३४५६७८९0-9]{1,3})", compact)
    if digit_match:
        value = int(digit_match.group(1).translate(DEVANAGARI_DIGITS))
        if 1 <= value <= 120:
            return value

    for chapter, patterns in CHAPTER_PATTERNS:
        if any(pattern in compact for pattern in patterns):
            return chapter
    return None


def normalize_for_match(value: str) -> str:
    return (
        value.replace("ऽ", "")
        .replace("'", "")
        .replace('"', "")
        .replace("।", "")
        .replace("॥", "")
        .replace("[", "")
        .replace("]", "")
        .replace(" ", "")
        .strip()
    )


def clean_marker(line: str) -> str:
    return " ".join(line.strip().strip("[]|*\"'").split())[:240]


def make_excerpt(text: str, max_chars: int = 900) -> str:
    compact = " ".join(text.split())
    return compact[:max_chars].strip()


def detect_verse_markers(text: str) -> list[str]:
    seen: set[str] = set()
    markers: list[str] = []
    for match in VERSE_MARKER_RE.finditer(text):
        marker = match.group(1).translate(DEVANAGARI_DIGITS)
        if marker not in seen:
            seen.add(marker)
            markers.append(marker)
    return markers


def import_sections(db: Session, sections: list[ParsedTatparyaSection], source_path: Path) -> int:
    imported = 0
    for section in sections:
        existing = (
            db.query(TatparyaReference)
            .filter(
                TatparyaReference.canto == section.canto,
                TatparyaReference.chapter == section.chapter,
                TatparyaReference.source_name == SOURCE_NAME,
            )
            .first()
        )
        values = {
            "marker_text": section.marker_text,
            "source_path": str(source_path),
            "ocr_language": OCR_LANGUAGE,
            "line_start": section.line_start,
            "line_end": section.line_end,
            "text": section.text,
            "text_excerpt": section.text_excerpt,
            "verse_markers": section.verse_markers,
            "parse_quality": section.parse_quality,
        }
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
        else:
            db.add(
                TatparyaReference(
                    canto=section.canto,
                    chapter=section.chapter,
                    source_name=SOURCE_NAME,
                    **values,
                )
            )
        imported += 1
    db.commit()
    return imported


def import_tatparya_ocr(source: Path, database_url: str | None = None, dry_run: bool = False) -> tuple[int, dict[int, int]]:
    sections = parse_ocr_text(source)
    counts: dict[int, int] = {}
    for section in sections:
        counts[section.canto] = counts.get(section.canto, 0) + 1

    if dry_run:
        return len(sections), counts

    if database_url:
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        target_engine = create_engine(database_url, connect_args=connect_args)
    else:
        target_engine = app_engine
    Base.metadata.create_all(bind=target_engine)
    with Session(target_engine) as db:
        imported = import_sections(db, sections, source)
    return imported, counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Import OCR text from Sri Bhagavata Tatparya Nirnaya.")
    parser.add_argument(
        "--source",
        default="backend/data/ocr/Sri_Bhagavata_Tatparya_Nirnaya_OCR.txt",
        help="Path to OCR sidecar text.",
    )
    parser.add_argument("--database-url", default=None, help="Override SQLAlchemy database URL.")
    parser.add_argument("--dry-run", action="store_true", help="Parse and report without writing to DB.")
    args = parser.parse_args()

    imported, counts = import_tatparya_ocr(Path(args.source), args.database_url, args.dry_run)
    print(f"{'Parsed' if args.dry_run else 'Imported'} {imported} Tatparya chapter references")
    for canto, count in sorted(counts.items()):
        print(f"  Canto {canto}: {count}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session, selectinload

from app.models.character import CharacterAlias, CharacterFeedback, CharacterForm, CharacterIdentity
from app.services.text import normalize_name


@dataclass
class CharacterMatch:
    character: CharacterIdentity
    matched_alias: str
    confidence: int


def list_characters(db: Session) -> list[CharacterIdentity]:
    return (
        db.query(CharacterIdentity)
        .options(selectinload(CharacterIdentity.aliases), selectinload(CharacterIdentity.forms))
        .order_by(CharacterIdentity.canonical_name.asc())
        .all()
    )


def resolve_characters(db: Session, text: str) -> tuple[list[CharacterMatch], list[str]]:
    normalized = f" {normalize_name(text)} "
    aliases = db.query(CharacterAlias).options(selectinload(CharacterAlias.character)).all()

    matches: dict[str, CharacterMatch] = {}
    for alias in aliases:
        needle = f" {alias.alias_normalized} "
        if needle in normalized:
            existing = matches.get(alias.character_id)
            if existing is None or alias.confidence > existing.confidence:
                matches[alias.character_id] = CharacterMatch(alias.character, alias.alias, alias.confidence)

    unknown = extract_possible_names(text)
    known_aliases = {normalize_name(m.matched_alias) for m in matches.values()}
    known_names = {normalize_name(m.character.canonical_name) for m in matches.values()}
    unknown = [
        name for name in unknown
        if normalize_name(name) not in known_aliases and normalize_name(name) not in known_names
    ]

    return list(matches.values()), unknown[:12]


def extract_possible_names(text: str) -> list[str]:
    candidates = re.findall(r"\b[A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]{2,}){0,2}\b", text or "")
    stop = {"The", "This", "Then", "When", "Where", "From", "Lord", "Sri", "Shri"}
    known_places = {
        "ayodhya",
        "dwaraka",
        "gokula",
        "govardhana",
        "mathura",
        "vaikuntha",
        "vrindavan",
        "yamuna",
    }
    seen: set[str] = set()
    names: list[str] = []
    for candidate in candidates:
        first = candidate.split()[0]
        if first in stop:
            continue
        key = normalize_name(candidate)
        if key in known_places:
            continue
        if key not in seen:
            seen.add(key)
            names.append(candidate)
    return names


def add_alias(db: Session, character_id: str, alias: str, confidence: int = 95, notes: str = "") -> CharacterAlias:
    obj = CharacterAlias(
        character_id=character_id,
        alias=alias.strip(),
        alias_normalized=normalize_name(alias),
        confidence=confidence,
        notes=notes,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def add_feedback(
    db: Session,
    character_id: str,
    note: str,
    feedback_type: str = "note",
    form_id: Optional[str] = None,
    asset_id: Optional[str] = None,
) -> CharacterFeedback:
    feedback = CharacterFeedback(
        character_id=character_id,
        form_id=form_id,
        asset_id=asset_id,
        feedback_type=feedback_type,
        note=note,
    )
    db.add(feedback)

    if form_id and feedback_type in {"visual_correction", "negative_prompt"}:
        form = db.get(CharacterForm, form_id)
        if form:
            form.negative_prompt = "\n".join([p for p in [form.negative_prompt, note] if p])

    db.commit()
    db.refresh(feedback)
    return feedback

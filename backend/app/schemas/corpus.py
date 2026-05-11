from typing import Optional

from pydantic import BaseModel


class ShlokaOut(BaseModel):
    id: str
    canto: int
    chapter: int
    verse: str
    sanskrit: str
    transliteration: str
    translation: str
    summary: str
    characters: list[str]
    location: str
    themes: list[str]
    source_name: str
    source_url: str
    license: str

    model_config = {"from_attributes": True}


class TatparyaReferenceOut(BaseModel):
    id: str
    canto: int
    chapter: int
    marker_text: str
    source_name: str
    source_path: str
    ocr_language: str
    line_start: int
    line_end: int
    text_excerpt: str
    verse_markers: list[str]
    parse_quality: str
    text: Optional[str] = None

    model_config = {"from_attributes": True}


class TatparyaStatsOut(BaseModel):
    total_references: int
    by_canto: dict[int, int]
    source_name: str

from sqlalchemy import JSON, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.character import new_id


class CorpusShloka(Base):
    __tablename__ = "corpus_shlokas"
    __table_args__ = (UniqueConstraint("canto", "chapter", "verse", name="uq_shloka_ref"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    canto: Mapped[int] = mapped_column(Integer, index=True)
    chapter: Mapped[int] = mapped_column(Integer, index=True)
    verse: Mapped[str] = mapped_column(String(40), index=True)
    sanskrit: Mapped[str] = mapped_column(Text, default="")
    transliteration: Mapped[str] = mapped_column(Text, default="")
    translation: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    characters: Mapped[list[str]] = mapped_column(JSON, default=list)
    location: Mapped[str] = mapped_column(String(160), default="")
    themes: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_name: Mapped[str] = mapped_column(String(160), default="")
    source_url: Mapped[str] = mapped_column(String(500), default="")
    license: Mapped[str] = mapped_column(String(160), default="")


class TatparyaReference(Base):
    __tablename__ = "tatparya_references"
    __table_args__ = (UniqueConstraint("canto", "chapter", "source_name", name="uq_tatparya_chapter_ref"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    canto: Mapped[int] = mapped_column(Integer, index=True)
    chapter: Mapped[int] = mapped_column(Integer, index=True)
    marker_text: Mapped[str] = mapped_column(String(240), default="")
    source_name: Mapped[str] = mapped_column(String(160), default="Sri Bhagavata Tatparya Nirnaya")
    source_path: Mapped[str] = mapped_column(String(500), default="")
    ocr_language: Mapped[str] = mapped_column(String(80), default="san+hin+eng")
    line_start: Mapped[int] = mapped_column(Integer, default=0)
    line_end: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text, default="")
    text_excerpt: Mapped[str] = mapped_column(Text, default="")
    verse_markers: Mapped[list[str]] = mapped_column(JSON, default=list)
    parse_quality: Mapped[str] = mapped_column(String(80), default="chapter_boundary")

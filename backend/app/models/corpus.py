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

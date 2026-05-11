from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.character import new_id, now_utc


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(240))
    source_mode: Mapped[str] = mapped_column(String(80), default="plot")
    input_text: Mapped[str] = mapped_column(Text, default="")
    source_refs: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    continuity_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    scenes: Mapped[list["EpisodeScene"]] = relationship(back_populates="episode", cascade="all, delete-orphan")


class EpisodeScene(Base):
    __tablename__ = "episode_scenes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    episode_id: Mapped[str] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), index=True)
    scene_number: Mapped[int] = mapped_column(Integer)
    source_refs: Mapped[list[str]] = mapped_column(JSON, default=list)
    narration: Mapped[str] = mapped_column(Text, default="")
    background: Mapped[str] = mapped_column(Text, default="")
    character_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    intensity: Mapped[str] = mapped_column(String(60), default="peaceful")
    image_prompt: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    episode: Mapped[Episode] = relationship(back_populates="scenes")

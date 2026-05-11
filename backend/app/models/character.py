from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class CharacterIdentity(Base):
    __tablename__ = "character_identities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    canonical_name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(80), default="character")
    description: Mapped[str] = mapped_column(Text, default="")
    source_notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    aliases: Mapped[list["CharacterAlias"]] = relationship(back_populates="character", cascade="all, delete-orphan")
    forms: Mapped[list["CharacterForm"]] = relationship(back_populates="character", cascade="all, delete-orphan")
    feedback: Mapped[list["CharacterFeedback"]] = relationship(back_populates="character", cascade="all, delete-orphan")


class CharacterAlias(Base):
    __tablename__ = "character_aliases"
    __table_args__ = (UniqueConstraint("alias_normalized", name="uq_character_alias_normalized"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    character_id: Mapped[str] = mapped_column(ForeignKey("character_identities.id", ondelete="CASCADE"), index=True)
    alias: Mapped[str] = mapped_column(String(160))
    alias_normalized: Mapped[str] = mapped_column(String(160), index=True)
    confidence: Mapped[int] = mapped_column(Integer, default=100)
    notes: Mapped[str] = mapped_column(Text, default="")

    character: Mapped[CharacterIdentity] = relationship(back_populates="aliases")


class CharacterForm(Base):
    __tablename__ = "character_forms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    character_id: Mapped[str] = mapped_column(ForeignKey("character_identities.id", ondelete="CASCADE"), index=True)
    form_name: Mapped[str] = mapped_column(String(160))
    age_stage: Mapped[str] = mapped_column(String(80), default="")
    visual_profile: Mapped[str] = mapped_column(Text, default="")
    cultural_rules: Mapped[str] = mapped_column(Text, default="")
    negative_prompt: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="draft")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    character: Mapped[CharacterIdentity] = relationship(back_populates="forms")
    assets: Mapped[list["CharacterAsset"]] = relationship(back_populates="form", cascade="all, delete-orphan")


class CharacterAsset(Base):
    __tablename__ = "character_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    form_id: Mapped[str] = mapped_column(ForeignKey("character_forms.id", ondelete="CASCADE"), index=True)
    asset_type: Mapped[str] = mapped_column(String(60), default="portrait")
    path: Mapped[str] = mapped_column(String(500))
    provider: Mapped[str] = mapped_column(String(80), default="grok-imagine")
    prompt: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    form: Mapped[CharacterForm] = relationship(back_populates="assets")
    feedback: Mapped[list["CharacterFeedback"]] = relationship(back_populates="asset")


class CharacterFeedback(Base):
    __tablename__ = "character_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    character_id: Mapped[str] = mapped_column(ForeignKey("character_identities.id", ondelete="CASCADE"), index=True)
    form_id: Mapped[Optional[str]] = mapped_column(ForeignKey("character_forms.id", ondelete="SET NULL"), nullable=True)
    asset_id: Mapped[Optional[str]] = mapped_column(ForeignKey("character_assets.id", ondelete="SET NULL"), nullable=True)
    feedback_type: Mapped[str] = mapped_column(String(80), default="note")
    note: Mapped[str] = mapped_column(Text)
    action_taken: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    character: Mapped[CharacterIdentity] = relationship(back_populates="feedback")
    asset: Mapped[Optional[CharacterAsset]] = relationship(back_populates="feedback")

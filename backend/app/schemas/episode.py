from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SceneOut(BaseModel):
    id: str
    episode_id: str
    scene_number: int
    source_refs: list[str]
    narration: str
    background: str
    character_ids: list[str]
    intensity: str
    image_prompt: str
    status: str

    model_config = {"from_attributes": True}


class EpisodeOut(BaseModel):
    id: str
    title: str
    source_mode: str
    input_text: str
    source_refs: list[str]
    status: str
    continuity_notes: str
    created_at: datetime
    scenes: list[SceneOut] = []

    model_config = {"from_attributes": True}


class EpisodePlanCreate(BaseModel):
    input_text: str = Field(min_length=5)
    source_mode: str = "plot"
    source_refs: list[str] = []
    target_scene_count: Optional[int] = Field(default=None, ge=3, le=24)


class SceneUpdate(BaseModel):
    narration: Optional[str] = None
    background: Optional[str] = None
    character_ids: Optional[list[str]] = None
    intensity: Optional[str] = None
    image_prompt: Optional[str] = None
    status: Optional[str] = None

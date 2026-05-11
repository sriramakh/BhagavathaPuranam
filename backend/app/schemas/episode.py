from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SceneCharacterAssetOut(BaseModel):
    id: str
    asset_type: str
    provider: str
    version: int
    approved: bool
    url: str


class SceneCharacterBriefOut(BaseModel):
    character_id: str
    canonical_name: str
    category: str
    form_id: Optional[str] = None
    form_name: str = ""
    visual_profile: str = ""
    cultural_rules: str = ""
    negative_prompt: str = ""
    reference_status: str
    reference_assets: list[SceneCharacterAssetOut] = Field(default_factory=list)


class SceneImageBriefOut(BaseModel):
    source_refs: list[str] = Field(default_factory=list)
    scene_description: str
    background: str
    intensity: str
    characters: list[SceneCharacterBriefOut] = Field(default_factory=list)
    previous_scene_context: list[str] = Field(default_factory=list)
    reference_requirements: list[str] = Field(default_factory=list)
    image_prompt: str


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
    image_brief: Optional[SceneImageBriefOut] = None

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
    scenes: list[SceneOut] = Field(default_factory=list)

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

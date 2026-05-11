from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CharacterAliasOut(BaseModel):
    id: str
    alias: str
    confidence: int
    notes: str

    model_config = {"from_attributes": True}


class CharacterAssetOut(BaseModel):
    id: str
    form_id: str
    asset_type: str
    path: str
    provider: str
    version: int
    approved: bool
    created_at: datetime
    url: Optional[str] = None

    model_config = {"from_attributes": True}


class CharacterFormOut(BaseModel):
    id: str
    character_id: str
    form_name: str
    age_stage: str
    visual_profile: str
    cultural_rules: str
    negative_prompt: str
    status: str
    is_default: bool
    assets: list[CharacterAssetOut] = []

    model_config = {"from_attributes": True}


class CharacterOut(BaseModel):
    id: str
    canonical_name: str
    category: str
    description: str
    source_notes: str
    status: str
    aliases: list[CharacterAliasOut] = []
    forms: list[CharacterFormOut] = []

    model_config = {"from_attributes": True}


class CharacterCreate(BaseModel):
    canonical_name: str = Field(min_length=2, max_length=160)
    category: str = "character"
    description: str = ""
    aliases: list[str] = []
    form_name: str = "Default Form"
    age_stage: str = ""
    visual_profile: str = ""
    cultural_rules: str = ""
    negative_prompt: str = ""


class CharacterFormCreate(BaseModel):
    form_name: str = Field(min_length=2, max_length=160)
    age_stage: str = ""
    visual_profile: str
    cultural_rules: str = ""
    negative_prompt: str = ""
    is_default: bool = False


class AliasCreate(BaseModel):
    alias: str = Field(min_length=2, max_length=160)
    confidence: int = 95
    notes: str = ""


class ResolveRequest(BaseModel):
    text: str


class ResolveMatchOut(BaseModel):
    character_id: str
    canonical_name: str
    matched_alias: str
    confidence: int


class ResolveResponse(BaseModel):
    matches: list[ResolveMatchOut]
    possible_new_characters: list[str]


class FeedbackCreate(BaseModel):
    character_id: str
    form_id: Optional[str] = None
    asset_id: Optional[str] = None
    feedback_type: str = "note"
    note: str


class FeedbackOut(BaseModel):
    id: str
    character_id: str
    form_id: Optional[str]
    asset_id: Optional[str]
    feedback_type: str
    note: str
    action_taken: str
    created_at: datetime

    model_config = {"from_attributes": True}

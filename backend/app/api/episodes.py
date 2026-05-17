from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.character import CharacterIdentity, CharacterForm
from app.models.episode import Episode, EpisodeScene
from app.schemas.episode import (
    EpisodeOut,
    EpisodePlanCreate,
    EpisodeStatusUpdate,
    SceneBatchUpdate,
    SceneOut,
    SceneUpdate,
)
from app.services.story_planner import create_episode_plan

router = APIRouter(prefix="/api/v1/episodes", tags=["episodes"])


def _asset_url(asset_id: str) -> str:
    return f"/api/v1/assets/{asset_id}"


def _default_form(character: CharacterIdentity) -> CharacterForm | None:
    if not character.forms:
        return None
    default = next((form for form in character.forms if form.is_default), None)
    return default or character.forms[0]


def _scene_characters(db: Session, character_ids: list[str]) -> list[dict]:
    if not character_ids:
        return []

    characters = (
        db.query(CharacterIdentity)
        .options(selectinload(CharacterIdentity.forms).selectinload(CharacterForm.assets))
        .filter(CharacterIdentity.id.in_(character_ids))
        .all()
    )
    by_id = {character.id: character for character in characters}
    briefs: list[dict] = []

    for character_id in character_ids:
        character = by_id.get(character_id)
        if not character:
            briefs.append(
                {
                    "character_id": character_id,
                    "canonical_name": "Unresolved character",
                    "category": "unknown",
                    "reference_status": "missing_character_profile",
                    "reference_requirements": [],
                }
            )
            continue

        form = _default_form(character)
        approved_assets = [asset for asset in (form.assets if form else []) if asset.approved]
        briefs.append(
            {
                "character_id": character.id,
                "canonical_name": character.canonical_name,
                "category": character.category,
                "form_id": form.id if form else None,
                "form_name": form.form_name if form else "",
                "visual_profile": form.visual_profile if form else character.description,
                "cultural_rules": form.cultural_rules if form else "",
                "negative_prompt": form.negative_prompt if form else "",
                "reference_status": "approved_reference_ready" if approved_assets else "profile_only_needs_approved_image",
                "reference_assets": [
                    {
                        "id": asset.id,
                        "asset_type": asset.asset_type,
                        "provider": asset.provider,
                        "version": asset.version,
                        "approved": asset.approved,
                        "url": _asset_url(asset.id),
                    }
                    for asset in approved_assets
                ],
            }
        )
    return briefs


def _previous_scene_context(db: Session, scene: EpisodeScene) -> list[str]:
    previous_scenes = (
        db.query(EpisodeScene)
        .filter(
            EpisodeScene.episode_id == scene.episode_id,
            EpisodeScene.scene_number < scene.scene_number,
        )
        .order_by(EpisodeScene.scene_number.desc())
        .limit(2)
        .all()
    )
    return [
        f"Scene {previous.scene_number}: {previous.narration} Background: {previous.background}. Generated image reference: pending until scene image generation is approved."
        for previous in reversed(previous_scenes)
    ]


def scene_to_response(db: Session, scene: EpisodeScene) -> dict:
    characters = _scene_characters(db, scene.character_ids or [])
    missing_refs = [
        f"{character['canonical_name']} needs an approved character image before final scene generation."
        for character in characters
        if character["reference_status"] != "approved_reference_ready"
    ]
    reference_requirements = [
        "Use approved character assets whenever available; otherwise use the stored visual profile exactly.",
        "Keep Indic mythological setting, attire, ornaments, architecture, landscape, and devotional tone.",
        "Depict divine combat or demon defeat symbolically and non-graphically when the scripture calls for it.",
        *missing_refs,
    ]
    return {
        "id": scene.id,
        "episode_id": scene.episode_id,
        "scene_number": scene.scene_number,
        "source_refs": scene.source_refs or [],
        "narration": scene.narration,
        "background": scene.background,
        "character_ids": scene.character_ids or [],
        "intensity": scene.intensity,
        "image_prompt": scene.image_prompt,
        "status": scene.status,
        "image_brief": {
            "source_refs": scene.source_refs or [],
            "scene_description": scene.narration,
            "background": scene.background,
            "intensity": scene.intensity,
            "characters": characters,
            "previous_scene_context": _previous_scene_context(db, scene),
            "reference_requirements": reference_requirements,
            "image_prompt": scene.image_prompt,
        },
    }


def episode_to_response(db: Session, episode: Episode) -> dict:
    scenes = sorted(episode.scenes, key=lambda item: item.scene_number)
    return {
        "id": episode.id,
        "title": episode.title,
        "source_mode": episode.source_mode,
        "input_text": episode.input_text,
        "source_refs": episode.source_refs or [],
        "status": episode.status,
        "continuity_notes": episode.continuity_notes,
        "created_at": episode.created_at,
        "scenes": [scene_to_response(db, scene) for scene in scenes],
    }


@router.get("", response_model=list[EpisodeOut])
def list_episodes(db: Session = Depends(get_db)):
    episodes = (
        db.query(Episode)
        .options(selectinload(Episode.scenes))
        .order_by(Episode.created_at.desc())
        .all()
    )
    return [episode_to_response(db, episode) for episode in episodes]


@router.post("/plan", response_model=EpisodeOut)
def plan_episode(payload: EpisodePlanCreate, db: Session = Depends(get_db)):
    episode = create_episode_plan(
        db,
        input_text=payload.input_text,
        source_mode=payload.source_mode,
        source_refs=payload.source_refs,
        target_scene_count=payload.target_scene_count,
        generation_mode=payload.generation_mode,
    )
    return episode_to_response(db, episode)


@router.get("/{episode_id}", response_model=EpisodeOut)
def get_episode(episode_id: str, db: Session = Depends(get_db)):
    episode = (
        db.query(Episode)
        .options(selectinload(Episode.scenes))
        .filter(Episode.id == episode_id)
        .first()
    )
    if not episode:
        raise HTTPException(404, "Episode not found")
    return episode_to_response(db, episode)


@router.patch("/{episode_id}/status", response_model=EpisodeOut)
def update_episode_status(episode_id: str, payload: EpisodeStatusUpdate, db: Session = Depends(get_db)):
    episode = (
        db.query(Episode)
        .options(selectinload(Episode.scenes))
        .filter(Episode.id == episode_id)
        .first()
    )
    if not episode:
        raise HTTPException(404, "Episode not found")
    if payload.status not in {"draft", "in_review", "approved", "archived"}:
        raise HTTPException(422, "Unsupported episode status")
    episode.status = payload.status
    db.commit()
    db.refresh(episode)
    return episode_to_response(db, episode)


@router.patch("/scenes/batch", response_model=list[SceneOut])
def batch_update_scenes(payload: SceneBatchUpdate, db: Session = Depends(get_db)):
    scenes = (
        db.query(EpisodeScene)
        .filter(EpisodeScene.id.in_(payload.scene_ids))
        .order_by(EpisodeScene.scene_number)
        .all()
    )
    if len(scenes) != len(set(payload.scene_ids)):
        raise HTTPException(404, "One or more scenes were not found")

    for scene in scenes:
        if payload.status:
            scene.status = payload.status
        if payload.intensity:
            scene.intensity = payload.intensity
        if payload.narration_instruction:
            scene.narration = append_revision_note(scene.narration, payload.narration_instruction)
        if payload.background_instruction:
            scene.background = append_revision_note(scene.background, payload.background_instruction)

    db.commit()
    for scene in scenes:
        db.refresh(scene)
    return [scene_to_response(db, scene) for scene in scenes]


@router.patch("/scenes/{scene_id}", response_model=SceneOut)
def update_scene(scene_id: str, payload: SceneUpdate, db: Session = Depends(get_db)):
    scene = db.get(EpisodeScene, scene_id)
    if not scene:
        raise HTTPException(404, "Scene not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(scene, key, value)
    db.commit()
    db.refresh(scene)
    return scene_to_response(db, scene)


def append_revision_note(value: str, instruction: str) -> str:
    note = instruction.strip()
    if not note:
        return value
    return f"{value.rstrip()}\n\nRevision direction: {note}"

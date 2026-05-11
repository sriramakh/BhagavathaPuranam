from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.session import get_db
from app.models.character import CharacterAlias, CharacterAsset, CharacterForm, CharacterIdentity
from app.schemas.character import (
    AliasCreate,
    CharacterCreate,
    CharacterFormCreate,
    CharacterOut,
    FeedbackCreate,
    FeedbackOut,
    ResolveRequest,
    ResolveResponse,
    ResolveMatchOut,
)
from app.services.character_memory import add_alias, add_feedback, list_characters, resolve_characters
from app.services.grok_image import ImageGenerationNotConfigured, generate_character_image
from app.services.text import normalize_name

router = APIRouter(prefix="/api/v1/characters", tags=["characters"])


def with_asset_urls(character: CharacterIdentity) -> CharacterIdentity:
    for form in character.forms:
        for asset in form.assets:
            asset.url = f"/api/v1/assets/{asset.id}"
    return character


@router.get("", response_model=list[CharacterOut])
def get_characters(db: Session = Depends(get_db)):
    return [with_asset_urls(c) for c in list_characters(db)]


@router.post("", response_model=CharacterOut)
def create_character(payload: CharacterCreate, db: Session = Depends(get_db)):
    existing = db.query(CharacterIdentity).filter(CharacterIdentity.canonical_name == payload.canonical_name).first()
    if existing:
        raise HTTPException(409, "Character already exists")

    character = CharacterIdentity(
        canonical_name=payload.canonical_name.strip(),
        category=payload.category,
        description=payload.description,
        status="draft",
    )
    db.add(character)
    db.flush()

    for alias in dict.fromkeys([payload.canonical_name, *payload.aliases]):
        db.add(
            CharacterAlias(
                character_id=character.id,
                alias=alias.strip(),
                alias_normalized=normalize_name(alias),
                confidence=100 if alias == payload.canonical_name else 95,
            )
        )

    db.add(
        CharacterForm(
            character_id=character.id,
            form_name=payload.form_name,
            age_stage=payload.age_stage,
            visual_profile=payload.visual_profile,
            cultural_rules=payload.cultural_rules,
            negative_prompt=payload.negative_prompt,
            is_default=True,
        )
    )
    db.commit()
    db.refresh(character)
    return with_asset_urls(character)


@router.post("/{character_id}/aliases", response_model=dict)
def create_alias(character_id: str, payload: AliasCreate, db: Session = Depends(get_db)):
    if not db.get(CharacterIdentity, character_id):
        raise HTTPException(404, "Character not found")
    alias = add_alias(db, character_id, payload.alias, payload.confidence, payload.notes)
    return {"id": alias.id, "alias": alias.alias, "confidence": alias.confidence}


@router.post("/{character_id}/forms", response_model=CharacterOut)
def create_form(character_id: str, payload: CharacterFormCreate, db: Session = Depends(get_db)):
    character = db.get(CharacterIdentity, character_id)
    if not character:
        raise HTTPException(404, "Character not found")
    if payload.is_default:
        db.query(CharacterForm).filter(CharacterForm.character_id == character_id).update({"is_default": False})
    db.add(CharacterForm(character_id=character_id, **payload.model_dump()))
    db.commit()
    character = (
        db.query(CharacterIdentity)
        .options(selectinload(CharacterIdentity.aliases), selectinload(CharacterIdentity.forms).selectinload(CharacterForm.assets))
        .filter(CharacterIdentity.id == character_id)
        .one()
    )
    return with_asset_urls(character)


@router.post("/resolve", response_model=ResolveResponse)
def resolve(payload: ResolveRequest, db: Session = Depends(get_db)):
    matches, unknown = resolve_characters(db, payload.text)
    return ResolveResponse(
        matches=[
            ResolveMatchOut(
                character_id=m.character.id,
                canonical_name=m.character.canonical_name,
                matched_alias=m.matched_alias,
                confidence=m.confidence,
            )
            for m in matches
        ],
        possible_new_characters=unknown,
    )


@router.post("/feedback", response_model=FeedbackOut)
def feedback(payload: FeedbackCreate, db: Session = Depends(get_db)):
    if not db.get(CharacterIdentity, payload.character_id):
        raise HTTPException(404, "Character not found")
    return add_feedback(
        db,
        character_id=payload.character_id,
        form_id=payload.form_id,
        asset_id=payload.asset_id,
        feedback_type=payload.feedback_type,
        note=payload.note,
    )


@router.post("/forms/{form_id}/generate-image", response_model=dict)
def generate_form_image(form_id: str, db: Session = Depends(get_db)):
    form = db.get(CharacterForm, form_id)
    if not form:
        raise HTTPException(404, "Character form not found")

    settings = get_settings()
    character_dir = Path(settings.storage_path) / "characters" / form.character_id / form.id
    version = db.query(CharacterAsset).filter(CharacterAsset.form_id == form.id).count() + 1
    output_path = character_dir / f"portrait_v{version}.png"

    try:
        path, prompt = generate_character_image(form, output_path)
    except ImageGenerationNotConfigured as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Grok Imagine generation failed: {exc}") from exc

    asset = CharacterAsset(
        form_id=form.id,
        asset_type="portrait",
        path=path,
        provider=settings.image_provider,
        prompt=prompt,
        version=version,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return {"asset_id": asset.id, "url": f"/api/v1/assets/{asset.id}", "prompt": prompt}


@router.post("/assets/{asset_id}/approve", response_model=dict)
def approve_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = db.get(CharacterAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")
    db.query(CharacterAsset).filter(CharacterAsset.form_id == asset.form_id).update({"approved": False})
    asset.approved = True
    form = db.get(CharacterForm, asset.form_id)
    if form:
        form.status = "approved"
    db.commit()
    return {"approved": True, "asset_id": asset.id}

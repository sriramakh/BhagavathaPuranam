from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.episode import Episode, EpisodeScene
from app.schemas.episode import EpisodeOut, EpisodePlanCreate, SceneOut, SceneUpdate
from app.services.story_planner import create_episode_plan

router = APIRouter(prefix="/api/v1/episodes", tags=["episodes"])


@router.get("", response_model=list[EpisodeOut])
def list_episodes(db: Session = Depends(get_db)):
    return (
        db.query(Episode)
        .options(selectinload(Episode.scenes))
        .order_by(Episode.created_at.desc())
        .all()
    )


@router.post("/plan", response_model=EpisodeOut)
def plan_episode(payload: EpisodePlanCreate, db: Session = Depends(get_db)):
    return create_episode_plan(
        db,
        input_text=payload.input_text,
        source_mode=payload.source_mode,
        source_refs=payload.source_refs,
        target_scene_count=payload.target_scene_count,
    )


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
    return episode


@router.patch("/scenes/{scene_id}", response_model=SceneOut)
def update_scene(scene_id: str, payload: SceneUpdate, db: Session = Depends(get_db)):
    scene = db.get(EpisodeScene, scene_id)
    if not scene:
        raise HTTPException(404, "Scene not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(scene, key, value)
    db.commit()
    db.refresh(scene)
    return scene

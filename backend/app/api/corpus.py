from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.corpus import CorpusShloka
from app.schemas.corpus import ShlokaOut

router = APIRouter(prefix="/api/v1/corpus", tags=["corpus"])


@router.get("/shlokas", response_model=list[ShlokaOut])
def list_shlokas(
    canto: Optional[int] = None,
    chapter: Optional[int] = None,
    q: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(CorpusShloka)
    if canto:
        query = query.filter(CorpusShloka.canto == canto)
    if chapter:
        query = query.filter(CorpusShloka.chapter == chapter)
    if q:
        like = f"%{q}%"
        query = query.filter(
            CorpusShloka.summary.ilike(like)
            | CorpusShloka.translation.ilike(like)
            | CorpusShloka.sanskrit.ilike(like)
        )
    return query.order_by(CorpusShloka.canto, CorpusShloka.chapter, CorpusShloka.verse).limit(100).all()

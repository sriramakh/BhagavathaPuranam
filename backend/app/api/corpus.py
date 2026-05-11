from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.corpus import CorpusShloka, TatparyaReference
from app.schemas.corpus import ShlokaOut, TatparyaReferenceOut, TatparyaStatsOut

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


@router.get("/tatparya", response_model=list[TatparyaReferenceOut])
def list_tatparya_references(
    canto: Optional[int] = None,
    chapter: Optional[int] = None,
    q: Optional[str] = Query(default=None),
    include_text: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(TatparyaReference)
    if canto:
        query = query.filter(TatparyaReference.canto == canto)
    if chapter:
        query = query.filter(TatparyaReference.chapter == chapter)
    if q:
        like = f"%{q}%"
        query = query.filter(TatparyaReference.text.ilike(like) | TatparyaReference.marker_text.ilike(like))

    references = query.order_by(TatparyaReference.canto, TatparyaReference.chapter).limit(200).all()
    return [tatparya_to_response(reference, include_text=include_text) for reference in references]


@router.get("/tatparya/stats", response_model=TatparyaStatsOut)
def tatparya_stats(db: Session = Depends(get_db)):
    rows = (
        db.query(TatparyaReference.canto, func.count(TatparyaReference.id))
        .group_by(TatparyaReference.canto)
        .order_by(TatparyaReference.canto)
        .all()
    )
    by_canto = {canto: count for canto, count in rows}
    return {
        "total_references": sum(by_canto.values()),
        "by_canto": by_canto,
        "source_name": "Sri Bhagavata Tatparya Nirnaya",
    }


@router.get("/tatparya/{reference_id}", response_model=TatparyaReferenceOut)
def get_tatparya_reference(reference_id: str, db: Session = Depends(get_db)):
    reference = db.get(TatparyaReference, reference_id)
    if not reference:
        raise HTTPException(404, "Tatparya reference not found")
    return tatparya_to_response(reference, include_text=True)


def tatparya_to_response(reference: TatparyaReference, include_text: bool = False) -> dict:
    return {
        "id": reference.id,
        "canto": reference.canto,
        "chapter": reference.chapter,
        "marker_text": reference.marker_text,
        "source_name": reference.source_name,
        "source_path": reference.source_path,
        "ocr_language": reference.ocr_language,
        "line_start": reference.line_start,
        "line_end": reference.line_end,
        "text_excerpt": reference.text_excerpt,
        "verse_markers": reference.verse_markers or [],
        "parse_quality": reference.parse_quality,
        "text": reference.text if include_text else None,
    }

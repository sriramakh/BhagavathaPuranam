from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.character import CharacterAsset

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


@router.get("/{asset_id}")
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = db.get(CharacterAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")
    return FileResponse(asset.path)

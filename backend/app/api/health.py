from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("")
def health():
    settings = get_settings()
    return {
        "ok": True,
        "app": settings.app_name,
        "image_provider": settings.image_provider,
        "content_domain": settings.content_domain,
        "mythology_mode": settings.mythology_mode,
    }

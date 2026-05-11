import base64
from pathlib import Path

import requests

from app.core.config import get_settings
from app.models.character import CharacterForm
from app.services.style_bible import INDIC_MYTHOLOGY_STYLE_BIBLE


class ImageGenerationNotConfigured(RuntimeError):
    pass


def build_character_prompt(form: CharacterForm) -> str:
    return f"""
{INDIC_MYTHOLOGY_STYLE_BIBLE}

Generate a clean approved character reference portrait for an animated Bhagavatham storybook.

Character form: {form.form_name}
Age/form: {form.age_stage}
Canonical visual profile: {form.visual_profile}
Cultural rules: {form.cultural_rules}

Composition:
- full body 3/4 view
- plain warm parchment or temple-neutral background
- bright devotional storybook quality
- consistent features suitable for reuse in future scenes
- no text, no logos, no modern objects

Avoid: {form.negative_prompt}
""".strip()


def generate_character_image(form: CharacterForm, output_path: Path) -> tuple[str, str]:
    settings = get_settings()
    if not settings.grok_api_key:
        raise ImageGenerationNotConfigured("GROK_API_KEY is not configured")

    prompt = build_character_prompt(form)
    body = {
        "model": settings.grok_image_model,
        "prompt": prompt,
        "n": 1,
        "response_format": "b64_json",
        "extra_body": {"aspect_ratio": "1:1", "resolution": "2k"},
    }
    response = requests.post(
        "https://api.x.ai/v1/images/generations",
        headers={
            "Authorization": f"Bearer {settings.grok_api_key}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=180,
    )
    response.raise_for_status()
    image_bytes = base64.b64decode(response.json()["data"][0]["b64_json"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)
    return str(output_path), prompt

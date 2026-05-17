from __future__ import annotations

import json
import re
from dataclasses import dataclass

import requests

from app.core.config import get_settings


class StoryGenerationUnavailable(RuntimeError):
    pass


@dataclass
class GrokScene:
    narration: str
    background: str
    intensity: str


def generate_story_scenes(
    story_input: str,
    scene_count: int,
    source_refs: list[str],
    source_contexts: list[str],
    tatparya_contexts: list[str],
    known_characters: list[str],
) -> list[GrokScene]:
    settings = get_settings()
    if not settings.grok_api_key:
        raise StoryGenerationUnavailable("GROK_API_KEY is not configured")

    response = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.grok_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.grok_chat_model,
            "temperature": 0.35,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a Bhagavatham episode planner for an animated devotional storybook. "
                        "Return strict JSON only. Write all public story text in English. "
                        "Use Indic mythological settings, not Western fantasy. Preserve scripture references, "
                        "avoid inventing doctrinal claims, and depict divine conflict symbolically without gore."
                    ),
                },
                {
                    "role": "user",
                    "content": _build_prompt(
                        story_input,
                        scene_count,
                        source_refs,
                        source_contexts,
                        tatparya_contexts,
                        known_characters,
                    ),
                },
            ],
        },
        timeout=settings.story_generation_timeout_seconds,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    data = _loads_json(content)
    scenes = data.get("scenes", [])
    if not isinstance(scenes, list) or not scenes:
        raise StoryGenerationUnavailable("Grok did not return scenes")

    parsed: list[GrokScene] = []
    for item in scenes[:scene_count]:
        if not isinstance(item, dict):
            continue
        narration = _clean_text(item.get("narration", ""))
        background = _clean_text(item.get("background", ""))
        intensity = str(item.get("intensity", "peaceful")).strip() or "peaceful"
        if narration and background:
            parsed.append(GrokScene(narration=narration, background=background, intensity=_normalize_intensity(intensity)))

    if len(parsed) < max(3, scene_count // 2):
        raise StoryGenerationUnavailable("Grok returned too few usable scenes")
    return parsed


def _build_prompt(
    story_input: str,
    scene_count: int,
    source_refs: list[str],
    source_contexts: list[str],
    tatparya_contexts: list[str],
    known_characters: list[str],
) -> str:
    return f"""
Create exactly {scene_count} scene beats for this Bhagavatham episode.

User story direction:
{story_input}

Source refs:
{", ".join(source_refs) if source_refs else "No explicit source refs"}

Curated English source summaries:
{chr(10).join(source_contexts) if source_contexts else "No curated English verse summaries available yet."}

Tatparya Nirnaya accuracy anchors:
{chr(10).join(tatparya_contexts) if tatparya_contexts else "No mapped Tatparya anchor available."}

Known recurring characters already in memory:
{", ".join(known_characters) if known_characters else "None matched yet"}

JSON schema:
{{
  "scenes": [
    {{
      "narration": "2-4 sentence English narration for this scene",
      "background": "English visual background description rooted in ancient Indic devotional setting",
      "intensity": "peaceful|tense|divine_victory"
    }}
  ]
}}

Rules:
- Scene 1 must clearly open the episode.
- The last scene must resolve with bhakti, protection, restoration, gratitude, or grace.
- Keep character names consistent with the known recurring character list.
- Include enough visual specificity for animation planning.
- Do not include Sanskrit, OCR text, verse text, markdown, headings, or commentary outside JSON.
""".strip()


def _loads_json(content: str) -> dict:
    cleaned = content.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        cleaned = fence.group(1).strip()
    return json.loads(cleaned)


def _clean_text(value: object) -> str:
    text = str(value or "").strip()
    return "".join(char for char in text if not ("\u0900" <= char <= "\u097f"))


def _normalize_intensity(value: str) -> str:
    normalized = value.lower().strip().replace("-", "_").replace(" ", "_")
    if normalized in {"divine_victory", "tense", "peaceful"}:
        return normalized
    if any(word in normalized for word in ["battle", "conflict", "victory", "protect"]):
        return "divine_victory"
    return "peaceful"

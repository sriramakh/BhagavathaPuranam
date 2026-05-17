from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.episode import Episode, EpisodeScene
from app.services.character_memory import resolve_characters
from app.services.grok_story import generate_story_scenes
from app.services.source_context import build_source_context
from app.services.style_bible import scene_prompt_base
from app.services.tatparya_lookup import tatparya_context_for_source_refs
from app.services.text import split_sentences, title_from_input


@dataclass
class PlannedBeat:
    narration: str
    background: str
    intensity: str


def create_episode_plan(
    db: Session,
    input_text: str,
    source_mode: str = "plot",
    source_refs: Optional[list[str]] = None,
    target_scene_count: Optional[int] = None,
    generation_mode: str = "grok",
) -> Episode:
    story_input = prepare_story_input(input_text)
    matches, unknown = resolve_characters(db, story_input)
    character_ids = [m.character.id for m in matches]
    source_context = build_source_context(db, source_refs or [])
    title = source_context.title if source_refs else title_from_input(story_input, fallback="Bhagavatham Episode")
    tatparya_contexts = tatparya_context_for_source_refs(db, source_refs or [])
    source_summaries = source_context.seed_summaries
    scene_count = target_scene_count or suggest_scene_count(story_input)
    planned_beats, engine_note = plan_scene_beats(
        story_input=story_input,
        scene_count=scene_count,
        source_refs=source_refs or [],
        source_contexts=source_summaries,
        tatparya_contexts=tatparya_contexts,
        known_characters=[m.character.canonical_name for m in matches],
        generation_mode=generation_mode,
    )

    episode = Episode(
        title=title,
        source_mode=source_mode,
        input_text=input_text,
        source_refs=source_refs or [],
        continuity_notes=(
            "Matched existing characters: "
            + ", ".join(m.character.canonical_name for m in matches)
            + (f". Possible new characters: {', '.join(unknown)}." if unknown else ".")
            + (
                f" Tatparya Nirnaya grounding available for {len(tatparya_contexts)} selected source chapter(s)."
                if tatparya_contexts
                else ""
            )
            + f" Planning engine: {engine_note}."
        ),
    )
    db.add(episode)
    db.flush()

    for index, beat in enumerate(planned_beats, start=1):
        intensity = beat.intensity or classify_intensity(beat.narration)
        background = beat.background or suggest_background(beat.narration)
        scene = EpisodeScene(
            episode_id=episode.id,
            scene_number=index,
            source_refs=source_refs or [],
            narration=beat.narration,
            background=background,
            character_ids=character_ids,
            intensity=intensity,
            image_prompt=build_scene_prompt(
                beat.narration,
                background,
                matches,
                intensity,
                source_refs or [],
                tatparya_contexts,
            ),
            status="draft",
        )
        db.add(scene)

    db.commit()
    db.refresh(episode)
    return episode


def suggest_scene_count(input_text: str) -> int:
    length = len(input_text or "")
    if length < 240:
        return 6
    if length < 700:
        return 8
    return 10


def title_from_refs(source_refs: Optional[list[str]]) -> str | None:
    refs = [ref for ref in (source_refs or []) if ref]
    if not refs:
        return None
    visible_refs = ", ".join(refs[:3])
    suffix = "..." if len(refs) > 3 else ""
    return f"Bhagavatham Episode: {visible_refs}{suffix}"


def plan_scene_beats(
    story_input: str,
    scene_count: int,
    source_refs: list[str],
    source_contexts: list[str],
    tatparya_contexts: list[str],
    known_characters: list[str],
    generation_mode: str = "grok",
) -> tuple[list[PlannedBeat], str]:
    settings = get_settings()
    requested_grok = generation_mode == "grok" and settings.story_generation_provider == "grok"
    if requested_grok:
        try:
            scenes = generate_story_scenes(
                story_input=story_input,
                scene_count=scene_count,
                source_refs=source_refs,
                source_contexts=source_contexts,
                tatparya_contexts=tatparya_contexts,
                known_characters=known_characters,
            )
            planned = [
                PlannedBeat(
                    narration=ensure_opening_or_resolution(scene.narration, index, len(scenes)),
                    background=scene.background,
                    intensity=scene.intensity,
                )
                for index, scene in enumerate(scenes[:scene_count], start=1)
            ]
            return normalize_scene_count(planned, scene_count), "grok story planner"
        except Exception:
            fallback = deterministic_beats(story_input, scene_count)
            return fallback, "deterministic fallback after Grok planner issue"

    return deterministic_beats(story_input, scene_count), "deterministic draft planner"


def deterministic_beats(input_text: str, scene_count: int) -> list[PlannedBeat]:
    return [
        PlannedBeat(
            narration=beat,
            background=suggest_background(beat),
            intensity=classify_intensity(beat),
        )
        for beat in create_beats(input_text, scene_count)
    ]


def normalize_scene_count(beats: list[PlannedBeat], scene_count: int) -> list[PlannedBeat]:
    if len(beats) >= scene_count:
        return beats[:scene_count]
    fallback = deterministic_beats("\n".join(beat.narration for beat in beats), scene_count)
    return (beats + fallback[len(beats):])[:scene_count]


def ensure_opening_or_resolution(text: str, index: int, total: int) -> str:
    lowered = text.lower()
    if index == 1 and "opens" not in lowered:
        return f"The episode opens with sacred focus and devotional atmosphere. {text}"
    if index == total and not any(word in lowered for word in ["closes", "resolves", "restored", "gratitude", "grace"]):
        return f"The episode resolves with bhakti, protection, and grace. {text}"
    return text


def prepare_story_input(input_text: str) -> str:
    story_lines: list[str] = []
    for raw_line in (input_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lowered = line.lower()
        if lowered.startswith("story premise:"):
            story_lines.append(line.split(":", 1)[1].strip())
            continue
        if lowered.startswith((
            "accuracy source:",
            "chapter marker:",
            "default story language:",
            "detected verse anchors:",
            "do not copy",
            "ocr language:",
            "source:",
            "story instruction:",
            "use the mapped",
            "verse markers detected:",
        )):
            continue
        if is_mostly_devanagari(line):
            continue
        story_lines.append(line)

    cleaned = "\n".join(story_lines).strip()
    return cleaned or "Create an English Bhagavatham episode from the selected scripture reference using Tatparya Nirnaya as the accuracy source."


def is_mostly_devanagari(text: str) -> bool:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return False
    devanagari = [char for char in letters if "\u0900" <= char <= "\u097f"]
    return len(devanagari) / len(letters) > 0.35


def create_beats(input_text: str, scene_count: int) -> list[str]:
    sentences = split_sentences(input_text)
    if not sentences:
        sentences = ["A sacred Bhagavatham episode unfolds with devotion and wonder."]

    if len(sentences) < scene_count:
        return expand_short_plot(sentences, scene_count)

    beats: list[str] = []
    for idx in range(scene_count):
        source = sentences[min(idx, len(sentences) - 1)]
        if idx == 0:
            beats.append(f"The episode opens in a devotional Indic setting. {source}")
        elif idx == scene_count - 1:
            beats.append(f"The episode resolves with bhakti, protection, and divine grace. {source}")
        else:
            beats.append(source)
    return beats


def expand_short_plot(sentences: list[str], scene_count: int) -> list[str]:
    opening = sentences[0]
    middle = sentences[len(sentences) // 2]
    ending = sentences[-1]
    templates = [
        f"The episode opens in a devotional Indic setting, establishing the sacred place and the main characters. {opening}",
        f"The characters move through the setting with warmth and purpose, revealing their relationships and mood. {opening}",
        f"A moment of wonder draws attention to the devotional heart of the episode. {middle}",
        f"The turning point begins, and the scene shifts from peaceful beauty toward divine purpose. {middle}",
        f"The challenge becomes clear in an epic but family-safe mythological way. {ending}",
        f"The divine response begins, showing courage, protection, and grace without graphic violence. {ending}",
        f"The conflict resolves symbolically, with the characters safe and the sacred setting restored. {ending}",
        f"The episode closes with bhakti, gratitude, and a clear emotional payoff rooted in the Bhagavatham. {ending}",
    ]
    if scene_count <= len(templates):
        return templates[:scene_count]
    extra = [
        f"A supporting visual beat deepens the Indic setting and character continuity. {middle}"
        for _ in range(scene_count - len(templates))
    ]
    return templates[:4] + extra + templates[4:]


def classify_intensity(text: str) -> str:
    low = (text or "").lower()
    if any(word in low for word in [
        "attack",
        "asura",
        "battle",
        "challenge",
        "demon",
        "divine victory",
        "fight",
        "kill",
        "protects",
        "slay",
        "subdue",
        "victory",
        "weapon",
    ]):
        return "divine_victory"
    if any(word in low for word in ["fear", "angry", "threat", "danger"]):
        return "tense"
    return "peaceful"


def suggest_background(text: str) -> str:
    low = (text or "").lower()
    if "vrindavan" in low or "gokula" in low:
        return "Vrindavan grove with Yamuna river atmosphere, kadamba trees, cows, peacocks, and warm devotional light"
    if "palace" in low or "king" in low:
        return "Indic royal palace hall with carved pillars, lamps, rangoli, and sacred ornamental details"
    if "forest" in low:
        return "Ancient Indian forest hermitage with banyan trees, flowering vines, deer, and soft golden light"
    if "river" in low or "yamuna" in low:
        return "Yamuna riverbank with lotus flowers, stone ghats, trees, cows, and sunset-gold devotional atmosphere"
    return "Ancient Indic devotional setting with temple details, lotus motifs, brass lamps, and warm storybook light"


def build_scene_prompt(
    beat: str,
    background: str,
    matches,
    intensity: str,
    source_refs: list[str],
    tatparya_contexts: list[str] | None = None,
) -> str:
    character_block = "\n".join(
        format_character_prompt_line(m)
        for m in matches
    ) or "- No approved recurring characters matched yet; create temporary culturally accurate characters only if needed."

    violence_rule = (
        "Render conflict as symbolic devotional epic action without gore, blood spray, horror, or graphic injury."
        if intensity in {"divine_victory", "tense"}
        else "Keep expressions devotional, warm, and storybook-friendly."
    )

    return f"""
{scene_prompt_base()}

Source references:
{", ".join(source_refs) if source_refs else "User-provided plot or unsourced draft"}

Tatparya Nirnaya accuracy anchors:
{chr(10).join(tatparya_contexts or []) if tatparya_contexts else "No Tatparya Nirnaya OCR reference mapped for this source yet."}

Default language:
Write all story-facing narration, image brief descriptions, and scene notes in English unless the user explicitly asks for Sanskrit.

Scene beat:
{beat}

Background:
{background}

Characters:
{character_block}

Intensity: {intensity}
{violence_rule}

Make this a polished animated storybook frame for Bhagavatham. No text, no logos, no modern objects.
""".strip()


def format_character_prompt_line(match) -> str:
    character = match.character
    default_form = None
    for form in character.forms:
        if form.is_default:
            default_form = form
            break
    if default_form is None and character.forms:
        default_form = character.forms[0]

    if default_form is None:
        return f"- {character.canonical_name}: use approved character identity and maintain continuity."

    return (
        f"- {character.canonical_name} ({default_form.form_name}): "
        f"{default_form.visual_profile} Cultural rules: {default_form.cultural_rules} "
        f"Avoid: {default_form.negative_prompt}"
    )

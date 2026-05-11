from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.episode import Episode, EpisodeScene
from app.services.character_memory import resolve_characters
from app.services.style_bible import scene_prompt_base
from app.services.tatparya_lookup import tatparya_context_for_source_refs
from app.services.text import split_sentences, title_from_input


def create_episode_plan(
    db: Session,
    input_text: str,
    source_mode: str = "plot",
    source_refs: Optional[list[str]] = None,
    target_scene_count: Optional[int] = None,
) -> Episode:
    matches, unknown = resolve_characters(db, input_text)
    character_ids = [m.character.id for m in matches]
    title = title_from_input(input_text, fallback="Bhagavatham Episode")
    tatparya_contexts = tatparya_context_for_source_refs(db, source_refs or [])

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
        ),
    )
    db.add(episode)
    db.flush()

    scene_count = target_scene_count or suggest_scene_count(input_text)
    beats = create_beats(input_text, scene_count)
    for index, beat in enumerate(beats, start=1):
        intensity = classify_intensity(beat)
        background = suggest_background(beat)
        scene = EpisodeScene(
            episode_id=episode.id,
            scene_number=index,
            source_refs=source_refs or [],
            narration=beat,
            background=background,
            character_ids=character_ids,
            intensity=intensity,
            image_prompt=build_scene_prompt(
                beat,
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

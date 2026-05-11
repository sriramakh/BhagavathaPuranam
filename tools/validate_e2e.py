#!/usr/bin/env python3
"""End-to-end validation for Bhagavatha Puranam planning.

The script validates the live API surface that the frontend uses:
- corpus search and source refs
- character alias resolution
- unknown character discovery
- episode scene planning
- recurring character IDs and visual prompt continuity
- mythology conflict intensity

Usage:
    python tools/validate_e2e.py --base-url http://46.28.44.35:8002
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from typing import Any

import requests


@dataclass
class Case:
    name: str
    text: str
    scene_count: int = 6
    source_refs: list[str] = field(default_factory=list)
    expected_characters: list[str] = field(default_factory=list)
    expected_unknowns: list[str] = field(default_factory=list)
    expected_intensity: str | None = None
    required_prompt_terms: list[str] = field(default_factory=list)


CASES = [
    Case(
        name="Invocation source opening",
        text="Source: SB 1.1.1\nSummary: Meditate on the Supreme Truth, the source and knower of all creation.",
        source_refs=["SB 1.1.1"],
        expected_characters=["Sri Krishna"],
        required_prompt_terms=["Source references", "SB 1.1.1"],
    ),
    Case(
        name="Kapila teaches Devahuti",
        text="Source: SB 3.25.21-44\nKapila teaches Devahuti about devotion, consciousness, and liberation in a hermitage.",
        source_refs=["SB 3.25.21-44"],
        expected_characters=["Kapila", "Devahuti"],
    ),
    Case(
        name="Prahlada nine forms of devotion",
        text="Source: SB 7.5.23-24\nPrahlada explains the nine forms of devotion while Hiranyakashipu questions him.",
        source_refs=["SB 7.5.23-24"],
        expected_characters=["Prahlada Maharaja", "Hiranyakashipu"],
    ),
    Case(
        name="Narasimha protects Prahlada",
        text="Source: SB 7.8.17-34\nNarasimha appears to protect Prahlada and defeat Hiranyakashipu in a symbolic divine victory.",
        source_refs=["SB 7.8.17-34"],
        expected_characters=["Prahlada Maharaja", "Narasimha", "Hiranyakashipu"],
        expected_intensity="divine_victory",
        required_prompt_terms=["without gore", "symbolic devotional epic"],
    ),
    Case(
        name="Putana episode",
        text="Source: SB 10.6.1-44\nPutana comes to Gokula, and baby Krishna protects himself and grants her liberation while Mother Yashoda and Nanda Maharaja are present.",
        source_refs=["SB 10.6.1-44"],
        expected_characters=["Sri Krishna", "Mother Yashoda", "Nanda Maharaja", "Putana"],
        expected_intensity="divine_victory",
    ),
    Case(
        name="Vrindavan entry",
        text="Source: SB 10.11.35-59\nKrishna and Balarama enter Vrindavan with Mother Yashoda, Nanda Maharaja, cowherd families, cows, and peacocks.",
        source_refs=["SB 10.11.35-59"],
        expected_characters=["Sri Krishna", "Balarama", "Mother Yashoda", "Nanda Maharaja"],
    ),
    Case(
        name="Govardhana protection",
        text="Source: SB 10.25.1-33\nKrishna lifts Govardhana Hill to protect Vrindavan from Indra's storm while Balarama, Mother Yashoda, and Nanda Maharaja shelter nearby.",
        source_refs=["SB 10.25.1-33"],
        expected_characters=["Sri Krishna", "Balarama", "Mother Yashoda", "Nanda Maharaja", "Indra"],
        expected_intensity="divine_victory",
    ),
    Case(
        name="Kanha alias and Govardhana",
        text="Kanha lifts Govardhana as Devendra sends heavy rain over Vrindavan.",
        expected_characters=["Sri Krishna", "Indra"],
        expected_intensity="divine_victory",
    ),
    Case(
        name="Narada alias with Kapila",
        text="Narad visits the hermitage where Lord Kapila teaches Mother Devahuti.",
        expected_characters=["Narada Muni", "Kapila", "Devahuti"],
    ),
    Case(
        name="Pootana alias",
        text="Pootana enters Gokula, but baby Krishna protects everyone with divine grace.",
        expected_characters=["Putana", "Sri Krishna"],
        expected_intensity="divine_victory",
    ),
    Case(
        name="Lord Narasimha alias",
        text="Lord Narasimha appears in the palace hall and protects Prahlad from Hiranyakashyap.",
        expected_characters=["Narasimha", "Prahlada Maharaja", "Hiranyakashipu"],
        expected_intensity="divine_victory",
    ),
    Case(
        name="Yashoda Maiya alias",
        text="Yashoda Maiya watches Gopala play by the Yamuna in Vrindavan.",
        expected_characters=["Mother Yashoda", "Sri Krishna"],
    ),
    Case(
        name="Devendra alias",
        text="Devendra sends a storm, and Krishna protects the cowherd village.",
        expected_characters=["Indra", "Sri Krishna"],
        expected_intensity="divine_victory",
    ),
    Case(
        name="Baladeva alias",
        text="Baladeva walks beside Govinda and the cowherd boys in Vrindavan.",
        expected_characters=["Balarama", "Sri Krishna"],
    ),
    Case(
        name="Unknown Akrura detection",
        text="Akrura comes to meet Krishna and Balarama in Mathura.",
        expected_characters=["Sri Krishna", "Balarama"],
        expected_unknowns=["Akrura"],
    ),
    Case(
        name="Unknown Dhruva detection",
        text="Dhruva prays in the forest with determination and devotion.",
        expected_unknowns=["Dhruva"],
    ),
    Case(
        name="Multiple source refs",
        text="Source: SB 7.5.23-24\nSource: SB 7.8.17-34\nPrahlada's devotion is tested, and Narasimha protects him.",
        source_refs=["SB 7.5.23-24", "SB 7.8.17-34"],
        expected_characters=["Prahlada Maharaja", "Narasimha"],
        expected_intensity="divine_victory",
    ),
    Case(
        name="No Western visual leakage",
        text="Krishna and Balarama play in Vrindavan near the Yamuna.",
        expected_characters=["Sri Krishna", "Balarama"],
        required_prompt_terms=["Avoid Western castles", "dhoti", "tilaka"],
    ),
    Case(
        name="Graphic violence prevention",
        text="Narasimha defeats Hiranyakashipu while protecting Prahlada.",
        expected_characters=["Narasimha", "Hiranyakashipu", "Prahlada Maharaja"],
        expected_intensity="divine_victory",
        required_prompt_terms=["without gore", "graphic injury"],
    ),
    Case(
        name="Scene expansion coherence",
        text="Krishna protects the people of Vrindavan during a storm.",
        scene_count=8,
        expected_characters=["Sri Krishna"],
        expected_intensity="divine_victory",
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    client = Client(args.base_url.rstrip("/"))
    failures: list[str] = []

    try:
        health = client.get("/api/v1/health")
        assert health["ok"] is True
    except Exception as exc:
        print(f"Health check failed: {exc}", file=sys.stderr)
        return 2

    characters = client.get("/api/v1/characters")
    char_by_name = {item["canonical_name"]: item["id"] for item in characters}

    failures.extend(validate_corpus(client))

    for case in CASES:
        failures.extend(validate_case(client, char_by_name, case))

    if failures:
        print("\nFAILURES")
        for failure in failures:
            print(f"- {failure}")
        print(f"\nResult: {len(CASES)} cases run, {len(failures)} failures")
        return 1

    print(f"All {len(CASES)} planning cases passed.")
    return 0


class Client:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get(self, path: str) -> Any:
        response = requests.get(f"{self.base_url}{path}", timeout=20)
        response.raise_for_status()
        return response.json()

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        response = requests.post(f"{self.base_url}{path}", json=payload, timeout=20)
        response.raise_for_status()
        return response.json()


def validate_corpus(client: Client) -> list[str]:
    failures: list[str] = []
    all_items = client.get("/api/v1/corpus/shlokas")
    if len(all_items) < 7:
        failures.append(f"Corpus should expose at least 7 seeded entries, got {len(all_items)}")

    govardhana = client.get("/api/v1/corpus/shlokas?q=Govardhana")
    if not any(item["canto"] == 10 and item["chapter"] == 25 for item in govardhana):
        failures.append("Corpus search for Govardhana did not return SB 10.25")

    prahlada = client.get("/api/v1/corpus/shlokas?q=Prahlada")
    refs = {(item["canto"], item["chapter"]) for item in prahlada}
    if (7, 5) not in refs or (7, 8) not in refs:
        failures.append("Corpus search for Prahlada should return SB 7.5 and SB 7.8")

    return failures


def validate_case(client: Client, char_by_name: dict[str, str], case: Case) -> list[str]:
    failures: list[str] = []
    prefix = case.name

    resolved = client.post("/api/v1/characters/resolve", {"text": case.text})
    resolved_names = {match["canonical_name"] for match in resolved["matches"]}
    unknowns = set(resolved["possible_new_characters"])

    for name in case.expected_characters:
        if name not in resolved_names:
            failures.append(f"{prefix}: expected character resolution for {name}, got {sorted(resolved_names)}")

    for name in case.expected_unknowns:
        if name not in unknowns:
            failures.append(f"{prefix}: expected unknown character {name}, got {sorted(unknowns)}")

    episode = client.post(
        "/api/v1/episodes/plan",
        {
            "input_text": case.text,
            "source_mode": "plot",
            "source_refs": case.source_refs,
            "target_scene_count": case.scene_count,
        },
    )

    scenes = sorted(episode["scenes"], key=lambda item: item["scene_number"])
    if len(scenes) != case.scene_count:
        failures.append(f"{prefix}: expected {case.scene_count} scenes, got {len(scenes)}")

    if episode["source_refs"] != case.source_refs:
        failures.append(f"{prefix}: source refs not preserved: {episode['source_refs']}")

    for scene in scenes:
        if not scene["narration"].strip():
            failures.append(f"{prefix}: scene {scene['scene_number']} has empty narration")
        if not scene["background"].strip():
            failures.append(f"{prefix}: scene {scene['scene_number']} has empty background")
        if "Create devotional Indic mythological storybook art" not in scene["image_prompt"]:
            failures.append(f"{prefix}: scene {scene['scene_number']} missing Indic style bible")

    for name in case.expected_characters:
        character_id = char_by_name.get(name)
        if character_id and not all(character_id in scene["character_ids"] for scene in scenes):
            failures.append(f"{prefix}: {name} ID not present in every planned scene")
        if name not in episode["continuity_notes"]:
            failures.append(f"{prefix}: {name} missing from continuity notes")

    if case.expected_intensity:
        if not any(scene["intensity"] == case.expected_intensity for scene in scenes):
            failures.append(f"{prefix}: expected at least one {case.expected_intensity} scene")

    all_prompts = "\n".join(scene["image_prompt"] for scene in scenes)
    for term in case.required_prompt_terms:
        if term not in all_prompts:
            failures.append(f"{prefix}: prompt missing required term {term!r}")

    unique_narrations = {scene["narration"] for scene in scenes}
    if len(unique_narrations) < max(3, len(scenes) // 2):
        failures.append(f"{prefix}: scene narrations are too repetitive")

    if scenes and "opens" not in scenes[0]["narration"].lower():
        failures.append(f"{prefix}: first scene should establish opening context")

    if scenes and len(scenes) >= 6 and not any(
        word in scenes[-1]["narration"].lower()
        for word in ["closes", "resolves", "restored", "gratitude", "grace"]
    ):
        failures.append(f"{prefix}: final scene lacks resolution language")

    return failures


if __name__ == "__main__":
    raise SystemExit(main())

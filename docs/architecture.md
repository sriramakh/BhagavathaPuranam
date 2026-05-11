# Architecture

## Core Loop

1. Seed or create canonical characters.
2. Generate one or more visual forms for each character.
3. Approve a form and reference image.
4. Select shloka(s), a known episode, or custom plot input.
5. Resolve all names against the character memory.
6. Create an editable episode scene plan.
7. Generate images only after scene approval.
8. Store feedback and use it in future prompts.

## Character Memory Model

Identity, form, and asset are separate.

- `CharacterIdentity`: who the character is.
- `CharacterAlias`: names and titles that map to that identity.
- `CharacterForm`: a specific depiction, such as baby Krishna, child Krishna, Narasimha form, or Narada as a travelling rishi.
- `CharacterAsset`: generated or uploaded reference image for a form.
- `CharacterFeedback`: user corrections and preferences that should influence future generation.

This lets the engine reuse the same approved Krishna when the same form appears again, while still supporting different legitimate forms.

## Story Planning

The planner produces an episode with scenes. Each scene stores:

- source references
- narration
- background
- character IDs
- intensity tag
- image prompt
- approval status

The frontend can edit one scene or a selected group of scenes before any image generation is run.

## Mythology Guardrails

Bhagavatham mode permits epic mythological conflict: gods, avatars, devas, asuras, divine weapons, battles, and slaying episodes. Prompts should render these events as devotional, symbolic, non-graphic scenes. The system avoids gore, horror realism, modern weapons, and exploitative violence.

## Corpus Sources

The repository is designed to ingest structured shloka data with source and license metadata. Recommended source handling:

- Store Sanskrit text from a source with clear license metadata.
- Store our own short summaries and plot beats.
- Avoid storing copyrighted modern translations unless explicitly licensed.
- Keep source URL, source name, license, canto, chapter, and verse on every row.

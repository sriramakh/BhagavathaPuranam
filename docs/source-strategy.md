# Bhagavatham Source Strategy

The product should distinguish scripture source text, translation, summary, and child-facing adaptation.

## Source Layers

1. `sanskrit`: original shloka text with source URL and license.
2. `translation`: only store translations with clear permission or public-domain status.
3. `summary`: our own concise episode-relevant meaning.
4. `plot_beats`: our own child-safe narrative beats for scene planning.
5. `visual_notes`: Indic setting, characters, mood, and object references.

## Candidate Resources

- GRETIL Bhāgavatapurāṇa Sanskrit text: useful as a structured Sanskrit base; record its license metadata before commercial use.
- Oxford Centre for Hindu Studies Bhagavata Purana Project: useful for scholarly orientation, bibliography, and context.
- Other Sanskrit indexes may be useful for cross-checking verse references, but should not be treated as licensing clearance for translations.

## Handling Short Story Plots

For each episode, the ingestion/planning layer should create:

- selected canto/chapter/verse refs
- literal context summary
- characters present
- location
- conflict or devotional turn
- child-facing narration style
- scene-count recommendation
- required recurring character IDs
- new character candidates

The generator should never silently invent a conflicting identity for an existing canonical character. Ambiguous names such as `Vasudeva`, `Rama`, or `Madhava` require context-based resolution or user confirmation.

"use client";

import { MessageSquarePlus, Plus, RefreshCcw, Sparkles, UserRoundCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { addCharacterFeedback, assetUrl, Character, createCharacter, listCharacters } from "@/lib/api";

const EMPTY_CHARACTER = {
  canonical_name: "",
  category: "character",
  description: "",
  aliases: "",
  form_name: "Default Form",
  age_stage: "",
  visual_profile: "",
  cultural_rules: "Use classical Indic/Puranic visual language. Avoid Western fantasy styling.",
  negative_prompt: "modern clothing, western fantasy, horror, gore, text, logos",
};

export function CharacterRegistry() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState(EMPTY_CHARACTER);
  const [feedback, setFeedback] = useState<Record<string, string>>({});

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setCharacters(await listCharacters());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load characters");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate() {
    if (!draft.canonical_name.trim() || !draft.visual_profile.trim()) {
      setError("Character name and visual profile are required.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await createCharacter({
        ...draft,
        aliases: draft.aliases.split(",").map((item) => item.trim()).filter(Boolean),
      });
      setDraft(EMPTY_CHARACTER);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create character");
    } finally {
      setLoading(false);
    }
  }

  async function saveFeedback(character: Character) {
    const note = feedback[character.id]?.trim();
    if (!note) return;
    setError(null);
    try {
      const defaultForm = character.forms.find((form) => form.is_default) || character.forms[0];
      await addCharacterFeedback({
        character_id: character.id,
        form_id: defaultForm?.id,
        feedback_type: "visual_correction",
        note,
      });
      setFeedback((current) => ({ ...current, [character.id]: "" }));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save feedback");
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">
            <UserRoundCheck size={20} />
            Character Memory
          </div>
          <div className="panel-copy">
            Canonical identities, aliases, reusable forms, and approved references for recurring Bhagavatham characters.
          </div>
        </div>
        <button className="button" onClick={load} disabled={loading} title="Refresh characters">
          <RefreshCcw size={16} />
          Refresh
        </button>
      </div>
      <div className="panel-body">
        {error && <div className="error">{error}</div>}
        <div className="character-create">
          <div className="scene-title">Create recurring character</div>
          <div className="character-create-grid">
            <input
              className="input"
              placeholder="Canonical name"
              value={draft.canonical_name}
              onChange={(event) => setDraft({ ...draft, canonical_name: event.target.value })}
            />
            <input
              className="input"
              placeholder="Aliases, comma separated"
              value={draft.aliases}
              onChange={(event) => setDraft({ ...draft, aliases: event.target.value })}
            />
            <select
              className="select"
              value={draft.category}
              onChange={(event) => setDraft({ ...draft, category: event.target.value })}
            >
              <option value="avatar">avatar</option>
              <option value="deva">deva</option>
              <option value="devotee">devotee</option>
              <option value="rishi">rishi</option>
              <option value="asura">asura</option>
              <option value="character">character</option>
            </select>
          </div>
          <textarea
            className="textarea compact"
            placeholder="Short identity description"
            value={draft.description}
            onChange={(event) => setDraft({ ...draft, description: event.target.value })}
          />
          <textarea
            className="textarea compact"
            placeholder="Approved visual profile to reuse across scenes"
            value={draft.visual_profile}
            onChange={(event) => setDraft({ ...draft, visual_profile: event.target.value })}
          />
          <div className="character-create-grid">
            <input
              className="input"
              placeholder="Form name"
              value={draft.form_name}
              onChange={(event) => setDraft({ ...draft, form_name: event.target.value })}
            />
            <input
              className="input"
              placeholder="Age/form"
              value={draft.age_stage}
              onChange={(event) => setDraft({ ...draft, age_stage: event.target.value })}
            />
            <button className="button primary" type="button" onClick={handleCreate} disabled={loading}>
              <Plus size={16} />
              Save Character
            </button>
          </div>
        </div>
        {loading ? (
          <div className="panel-copy">Loading character memory...</div>
        ) : (
          <div className="character-grid">
            {characters.map((character) => {
              const defaultForm = character.forms.find((form) => form.is_default) || character.forms[0];
              const approvedAsset = defaultForm?.assets.find((asset) => asset.approved) || defaultForm?.assets[0];
              return (
                <article className="character-card" key={character.id}>
                  <div className="character-top">
                    <div>
                      <div className="character-name">{character.canonical_name}</div>
                      <div className="panel-copy">{character.description}</div>
                    </div>
                    <span className="tag">{character.category}</span>
                  </div>

                  {approvedAsset && (
                    <img
                      src={assetUrl(approvedAsset)}
                      alt={`${character.canonical_name} approved reference`}
                      style={{
                        width: "100%",
                        aspectRatio: "1 / 1",
                        objectFit: "cover",
                        borderRadius: 8,
                        marginTop: 12,
                        border: "1px solid var(--line)",
                      }}
                    />
                  )}

                  <div className="small-list">
                    {character.aliases.slice(0, 6).map((alias) => (
                      <span className="tag" key={alias.id}>{alias.alias}</span>
                    ))}
                  </div>

                  {defaultForm && (
                    <div className="form-block">
                      <div className="form-title">{defaultForm.form_name}</div>
                      <div className="form-text">{defaultForm.visual_profile}</div>
                      <div className="small-list">
                        <span className="tag">{defaultForm.status}</span>
                        {defaultForm.assets.length === 0 && (
                          <span className="tag">
                            <Sparkles size={12} />
                            ready for portrait
                          </span>
                        )}
                      </div>
                      <div className="feedback-row">
                        <input
                          className="input"
                          placeholder="Add learning note for future scenes..."
                          value={feedback[character.id] || ""}
                          onChange={(event) => setFeedback((current) => ({ ...current, [character.id]: event.target.value }))}
                        />
                        <button className="icon-button" title="Save feedback" onClick={() => saveFeedback(character)}>
                          <MessageSquarePlus size={15} />
                        </button>
                      </div>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}

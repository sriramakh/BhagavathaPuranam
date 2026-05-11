"use client";

import { RefreshCcw, Sparkles, UserRoundCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { assetUrl, Character, listCharacters } from "@/lib/api";

export function CharacterRegistry() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

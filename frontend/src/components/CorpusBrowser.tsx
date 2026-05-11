"use client";

import { BookOpenText, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { listShlokas, Shloka } from "@/lib/api";
import type { SelectedSource } from "@/components/StudioWorkspace";

export function CorpusBrowser({ onUseSource }: { onUseSource: (source: SelectedSource) => void }) {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<Shloka[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load(nextQuery = query) {
    setLoading(true);
    setError(null);
    try {
      setItems(await listShlokas({ q: nextQuery || undefined }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load repository");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load("");
  }, []);

  function sourceText(item: Shloka) {
    const ref = `SB ${item.canto}.${item.chapter}.${item.verse}`;
    return [
      `Source: ${ref}`,
      `Location: ${item.location}`,
      `Characters: ${item.characters.join(", ")}`,
      `Themes: ${item.themes.join(", ")}`,
      `Summary: ${item.summary}`,
    ].join("\n");
  }

  return (
    <section className="panel corpus-panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">
            <BookOpenText size={20} />
            Bhagavatham Repository
          </div>
          <div className="panel-copy">
            Browse source references and episode summaries. Select entries to feed the planner with canonical refs, characters, location, and themes.
          </div>
          <div className="planner-note">
            This is a curated seed repository, not the full Bhagavatham corpus yet. Full shloka and translation ingestion is the next source-pipeline step after licensing/source selection.
          </div>
        </div>
      </div>
      <div className="panel-body">
        <form
          className="search-row"
          onSubmit={(event) => {
            event.preventDefault();
            load();
          }}
        >
          <input
            className="input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search Krishna, Prahlada, Govardhana, devotion..."
          />
          <button className="button" type="submit" disabled={loading}>
            <Search size={16} />
            Search
          </button>
        </form>

        {error && <div className="error">{error}</div>}
        {loading ? (
          <div className="panel-copy">Loading repository...</div>
        ) : (
          <>
            <div className="repository-status">
              Showing {items.length} curated source {items.length === 1 ? "entry" : "entries"}.
            </div>
            <div className="corpus-list">
              {items.map((item) => {
                const ref = `SB ${item.canto}.${item.chapter}.${item.verse}`;
                return (
                  <article className="corpus-card" key={item.id}>
                    <div className="corpus-top">
                      <div>
                        <div className="character-name">{ref}</div>
                        <div className="panel-copy">{item.location}</div>
                      </div>
                      <button
                        className="button accent"
                        onClick={() => onUseSource({ ref, text: sourceText(item) })}
                      >
                        Use
                      </button>
                    </div>
                    <p className="scene-text">{item.summary}</p>
                    <div className="small-list">
                      {item.characters.map((character) => (
                        <span className="tag" key={character}>{character}</span>
                      ))}
                    </div>
                    <div className="small-list">
                      {item.themes.map((theme) => (
                        <span className="tag" key={theme}>{theme}</span>
                      ))}
                    </div>
                    <div className="license-note">{item.license}</div>
                  </article>
                );
              })}
            </div>
          </>
        )}
      </div>
    </section>
  );
}

"use client";

import { BookOpenText, Library, Search } from "lucide-react";
import { useEffect, useState } from "react";
import {
  getTatparyaStats,
  listShlokas,
  listTatparyaReferences,
  Shloka,
  TatparyaReference,
  TatparyaStats,
} from "@/lib/api";
import type { SelectedSource } from "@/components/StudioWorkspace";

type CorpusMode = "seeds" | "tatparya";

export function CorpusBrowser({ onUseSource }: { onUseSource: (source: SelectedSource) => void }) {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<CorpusMode>("tatparya");
  const [items, setItems] = useState<Shloka[]>([]);
  const [tatparyaItems, setTatparyaItems] = useState<TatparyaReference[]>([]);
  const [tatparyaStats, setTatparyaStats] = useState<TatparyaStats | null>(null);
  const [canto, setCanto] = useState<number | "all">("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load(nextQuery = query, nextMode = mode, nextCanto = canto) {
    setLoading(true);
    setError(null);
    try {
      if (nextMode === "tatparya") {
        const [refs, stats] = await Promise.all([
          listTatparyaReferences({
            q: nextQuery || undefined,
            canto: nextCanto === "all" ? undefined : nextCanto,
          }),
          getTatparyaStats(),
        ]);
        setTatparyaItems(refs);
        setTatparyaStats(stats);
      } else {
        setItems(await listShlokas({ q: nextQuery || undefined }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load repository");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load("", "tatparya", "all");
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

  function tatparyaSourceText(item: TatparyaReference) {
    const ref = `SB ${item.canto}.${item.chapter}`;
    return [
      `Source: ${ref}`,
      `Accuracy source: ${item.source_name}`,
      `OCR language: ${item.ocr_language}`,
      `Chapter marker: ${item.marker_text}`,
      `Verse markers detected: ${item.verse_markers.slice(0, 24).join(", ") || "chapter-level reference"}`,
      `Tatparya excerpt: ${item.text_excerpt}`,
    ].join("\n");
  }

  function switchMode(nextMode: CorpusMode) {
    setMode(nextMode);
    setQuery("");
    setCanto("all");
    load("", nextMode, "all");
  }

  function changeCanto(value: string) {
    const nextCanto = value === "all" ? "all" : Number(value);
    setCanto(nextCanto);
    load(query, mode, nextCanto);
  }

  const totalTatparya = tatparyaStats?.total_references ?? tatparyaItems.length;
  const shownCount = mode === "tatparya" ? tatparyaItems.length : items.length;

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
            Tatparya Nirnaya is now available as the accuracy layer from OCR. The curated seed list is still separate and contains only starter story summaries.
          </div>
        </div>
      </div>
      <div className="panel-body">
        <div className="repository-tabs" role="tablist" aria-label="Corpus layers">
          <button
            className={`tab-button ${mode === "tatparya" ? "active" : ""}`}
            onClick={() => switchMode("tatparya")}
            type="button"
            role="tab"
            aria-selected={mode === "tatparya"}
          >
            <Library size={15} />
            Tatparya Nirnaya
            <span>{totalTatparya || 115}</span>
          </button>
          <button
            className={`tab-button ${mode === "seeds" ? "active" : ""}`}
            onClick={() => switchMode("seeds")}
            type="button"
            role="tab"
            aria-selected={mode === "seeds"}
          >
            <BookOpenText size={15} />
            Story Seeds
            <span>{items.length || 7}</span>
          </button>
        </div>

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
            placeholder={mode === "tatparya" ? "Search Tatparya OCR text..." : "Search Krishna, Prahlada, Govardhana, devotion..."}
          />
          {mode === "tatparya" && (
            <select
              className="select compact-select"
              value={canto}
              onChange={(event) => changeCanto(event.target.value)}
              aria-label="Filter skanda"
            >
              <option value="all">All skandas</option>
              {Array.from({ length: 12 }, (_, index) => index + 1).map((value) => (
                <option value={value} key={value}>
                  Skanda {value}{tatparyaStats?.by_canto[String(value)] ? ` (${tatparyaStats.by_canto[String(value)]})` : ""}
                </option>
              ))}
            </select>
          )}
          <button className="button" type="submit" disabled={loading}>
            <Search size={16} />
            Search
          </button>
        </form>

        {error && <div className="error">{error}</div>}
        {loading ? (
          <div className="panel-copy">Loading repository...</div>
        ) : mode === "tatparya" ? (
          <>
            <div className="repository-status">
              Showing {shownCount} Tatparya Nirnaya reference {shownCount === 1 ? "chapter" : "chapters"} from {totalTatparya} mapped OCR references.
            </div>
            <div className="corpus-list">
              {tatparyaItems.map((item) => {
                const ref = `SB ${item.canto}.${item.chapter}`;
                return (
                  <article className="corpus-card" key={item.id}>
                    <div className="corpus-top">
                      <div>
                        <div className="character-name">{ref}</div>
                        <div className="panel-copy">{item.marker_text}</div>
                      </div>
                      <button
                        className="button accent"
                        onClick={() => onUseSource({ ref, text: tatparyaSourceText(item) })}
                      >
                        Use
                      </button>
                    </div>
                    <p className="scene-text">{item.text_excerpt}</p>
                    <div className="small-list">
                      <span className="tag">Skanda {item.canto}</span>
                      <span className="tag">Chapter {item.chapter}</span>
                      <span className="tag">{item.parse_quality.replaceAll("_", " ")}</span>
                    </div>
                    <div className="small-list">
                      {item.verse_markers.slice(0, 12).map((marker) => (
                        <span className="tag" key={marker}>verse {marker}</span>
                      ))}
                      {item.verse_markers.length > 12 && (
                        <span className="tag">+{item.verse_markers.length - 12} more</span>
                      )}
                    </div>
                    <div className="license-note">
                      OCR reference from {item.source_name}; use as accuracy grounding, not final public display text.
                    </div>
                  </article>
                );
              })}
            </div>
          </>
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

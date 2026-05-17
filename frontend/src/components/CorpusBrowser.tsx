"use client";

import { BookOpenText, CheckCircle2, Library, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  getTatparyaStats,
  getShlokaStats,
  listShlokas,
  listTatparyaReferences,
  ShlokaStats,
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
  const [shlokaStats, setShlokaStats] = useState<ShlokaStats | null>(null);
  const [canto, setCanto] = useState<number | "all">("all");
  const [selectedTatparyaId, setSelectedTatparyaId] = useState<string | null>(null);
  const [selectedSeedId, setSelectedSeedId] = useState<string | null>(null);
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
        setSelectedTatparyaId((current) => (current && refs.some((item) => item.id === current) ? current : refs[0]?.id ?? null));
      } else {
        const [seeds, stats] = await Promise.all([
          listShlokas({ q: nextQuery || undefined }),
          getShlokaStats(),
        ]);
        setItems(seeds);
        setShlokaStats(stats);
        setSelectedSeedId((current) => (current && seeds.some((item) => item.id === current) ? current : seeds[0]?.id ?? null));
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
      item.translation ? `English translation: ${item.translation}` : "",
    ].filter(Boolean).join("\n");
  }

  function tatparyaSourceText(item: TatparyaReference) {
    const ref = `SB ${item.canto}.${item.chapter}`;
    return [
      `Source: ${ref}`,
      "Default story language: English",
      `Story premise: Create an English Bhagavatham episode from ${ref}, using Tatparya Nirnaya as the accuracy reference.`,
      "Story instruction: Write all narration, scene descriptions, character dialogue notes, and image brief explanations in English unless the user explicitly asks for Sanskrit.",
      `Accuracy source: ${item.source_name}`,
      "Use the mapped Tatparya Nirnaya OCR reference as internal doctrinal and interpretive grounding.",
      "Do not copy Sanskrit/OCR text into the story output.",
      `Detected verse anchors: ${item.verse_markers.slice(0, 24).join(", ") || "chapter-level reference"}`,
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
  const totalShlokas = shlokaStats?.total_verses ?? items.length;
  const shownCount = mode === "tatparya" ? tatparyaItems.length : items.length;
  const selectedTatparya = useMemo(
    () => tatparyaItems.find((item) => item.id === selectedTatparyaId) ?? tatparyaItems[0] ?? null,
    [selectedTatparyaId, tatparyaItems],
  );
  const selectedSeed = useMemo(
    () => items.find((item) => item.id === selectedSeedId) ?? items[0] ?? null,
    [selectedSeedId, items],
  );

  return (
    <section className="panel corpus-panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">
            <BookOpenText size={20} />
            Bhagavatham Repository
          </div>
          <div className="panel-copy">
            Pick a scripture reference without scrolling through walls of OCR text. Tatparya is used for accuracy; stories are drafted in English by default.
          </div>
        </div>
      </div>
      <div className="panel-body">
        <div className="repository-shell">
          <div className="repository-tools">
            <div className="repository-tabs" role="tablist" aria-label="Corpus layers">
              <button
                className={`tab-button ${mode === "tatparya" ? "active" : ""}`}
                onClick={() => switchMode("tatparya")}
                type="button"
                role="tab"
                aria-selected={mode === "tatparya"}
              >
                <Library size={15} />
                Tatparya
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
                Seeds
                <span>{totalShlokas || 7}</span>
              </button>
            </div>

            <form
              className="source-search"
              onSubmit={(event) => {
                event.preventDefault();
                load();
              }}
            >
              <input
                className="input"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={mode === "tatparya" ? "Search OCR reference..." : "Search story seeds..."}
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

            <div className="repository-status">
              {mode === "tatparya"
                ? `${shownCount} of ${totalTatparya} Tatparya references`
                : `${shownCount} of ${totalShlokas} English verse records`}
            </div>
          </div>

          {error && <div className="error">{error}</div>}
          {loading ? (
            <div className="panel-copy">Loading repository...</div>
          ) : mode === "tatparya" ? (
            <div className="source-explorer">
              <div className="source-list" aria-label="Tatparya references">
                {tatparyaItems.map((item) => {
                  const ref = `SB ${item.canto}.${item.chapter}`;
                  const selected = selectedTatparya?.id === item.id;
                  return (
                    <button
                      className={`source-row ${selected ? "active" : ""}`}
                      key={item.id}
                      type="button"
                      onClick={() => setSelectedTatparyaId(item.id)}
                    >
                      <span className="source-ref">{ref}</span>
                      <span className="source-meta">Skanda {item.canto} · Chapter {item.chapter}</span>
                      <span className="source-tags">
                        {item.verse_markers.length > 0 ? `${item.verse_markers.length} verse anchors` : "chapter-level"}
                      </span>
                    </button>
                  );
                })}
              </div>

              <div className="source-detail">
                {selectedTatparya ? (
                  <>
                    <div className="detail-kicker">Tatparya accuracy source</div>
                    <div className="detail-title">SB {selectedTatparya.canto}.{selectedTatparya.chapter}</div>
                    <p className="detail-copy">
                      This reference is mapped from Madhwacharya&apos;s Tatparya Nirnaya OCR and will ground the planner internally. The story draft stays in English.
                    </p>
                    <div className="detail-grid">
                      <div>
                        <span>Skanda</span>
                        <strong>{selectedTatparya.canto}</strong>
                      </div>
                      <div>
                        <span>Chapter</span>
                        <strong>{selectedTatparya.chapter}</strong>
                      </div>
                      <div>
                        <span>Verse Anchors</span>
                        <strong>{selectedTatparya.verse_markers.length || "Chapter"}</strong>
                      </div>
                    </div>
                    <div className="small-list">
                      {selectedTatparya.verse_markers.slice(0, 16).map((marker) => (
                        <span className="tag" key={marker}>verse {marker}</span>
                      ))}
                      {selectedTatparya.verse_markers.length > 16 && (
                        <span className="tag">+{selectedTatparya.verse_markers.length - 16} more</span>
                      )}
                    </div>
                    <div className="english-default">
                      <CheckCircle2 size={15} />
                      English narration and scene descriptions by default
                    </div>
                    <details className="source-technical">
                      <summary>OCR marker</summary>
                      <div>{selectedTatparya.marker_text}</div>
                    </details>
                    <button
                      className="button primary"
                      onClick={() => onUseSource({
                        ref: `SB ${selectedTatparya.canto}.${selectedTatparya.chapter}`,
                        text: tatparyaSourceText(selectedTatparya),
                      })}
                    >
                      Use Selected Reference
                    </button>
                  </>
                ) : (
                  <div className="panel-copy">No Tatparya reference selected.</div>
                )}
              </div>
            </div>
          ) : (
            <div className="source-explorer">
              <div className="source-list" aria-label="Story seed references">
                {items.map((item) => {
                  const ref = `SB ${item.canto}.${item.chapter}.${item.verse}`;
                  const selected = selectedSeed?.id === item.id;
                  return (
                    <button
                      className={`source-row ${selected ? "active" : ""}`}
                      key={item.id}
                      type="button"
                      onClick={() => setSelectedSeedId(item.id)}
                    >
                      <span className="source-ref">{ref}</span>
                      <span className="source-meta">{item.location || "Curated story seed"}</span>
                      <span className="source-tags">{item.characters.slice(0, 3).join(", ")}</span>
                    </button>
                  );
                })}
              </div>

              <div className="source-detail">
                {selectedSeed ? (
                  <>
                    <div className="detail-kicker">Curated story seed</div>
                    <div className="detail-title">SB {selectedSeed.canto}.{selectedSeed.chapter}.{selectedSeed.verse}</div>
                    <p className="detail-copy">{selectedSeed.summary}</p>
                    {selectedSeed.translation && (
                      <details className="source-technical">
                        <summary>English translation</summary>
                        <div>{selectedSeed.translation}</div>
                      </details>
                    )}
                    <div className="small-list">
                      {selectedSeed.characters.map((character) => (
                        <span className="tag" key={character}>{character}</span>
                      ))}
                    </div>
                    <div className="small-list">
                      {selectedSeed.themes.map((theme) => (
                        <span className="tag" key={theme}>{theme}</span>
                      ))}
                    </div>
                    <button
                      className="button primary"
                      onClick={() => onUseSource({
                        ref: `SB ${selectedSeed.canto}.${selectedSeed.chapter}.${selectedSeed.verse}`,
                        text: sourceText(selectedSeed),
                      })}
                    >
                      Use Selected Seed
                    </button>
                    <div className="license-note">{selectedSeed.license}</div>
                  </>
                ) : (
                  <div className="panel-copy">No story seed selected.</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

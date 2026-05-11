"use client";

import { BookMarked, CircleCheck, ScanSearch, WandSparkles } from "lucide-react";
import { useState } from "react";
import { createEpisodePlan, Episode, resolveCharacters, ResolveResponse } from "@/lib/api";

const SAMPLE = "Krishna and Balarama enter Vrindavan with the cowherd boys. Mother Yashoda watches with love as Krishna plays his flute near the Yamuna. A demon appears and Krishna protects everyone with divine grace.";

export function EpisodePlanner() {
  const [text, setText] = useState(SAMPLE);
  const [sceneCount, setSceneCount] = useState(8);
  const [resolveResult, setResolveResult] = useState<ResolveResponse | null>(null);
  const [episode, setEpisode] = useState<Episode | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleResolve() {
    setLoading("resolve");
    setError(null);
    try {
      setResolveResult(await resolveCharacters(text));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Resolution failed");
    } finally {
      setLoading(null);
    }
  }

  async function handlePlan() {
    setLoading("plan");
    setError(null);
    try {
      const next = await createEpisodePlan(text, sceneCount);
      setEpisode(next);
      setResolveResult({
        matches: [],
        possible_new_characters: [],
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Planning failed");
    } finally {
      setLoading(null);
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">
            <BookMarked size={20} />
            Episode Planner
          </div>
          <div className="panel-copy">
            Start from a shloka group, episode summary, or custom plot. The engine resolves recurring characters before building editable scenes.
          </div>
        </div>
      </div>
      <div className="panel-body">
        <div className="field">
          <label htmlFor="plot">Source shloka summary or plot input</label>
          <textarea
            id="plot"
            className="textarea"
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="scene-count">Target scenes</label>
          <select
            id="scene-count"
            className="select"
            value={sceneCount}
            onChange={(event) => setSceneCount(Number(event.target.value))}
          >
            {[6, 8, 10, 12, 16].map((value) => (
              <option value={value} key={value}>{value} scenes</option>
            ))}
          </select>
        </div>

        <div className="toolbar">
          <button className="button" onClick={handleResolve} disabled={!!loading}>
            <ScanSearch size={16} />
            Resolve Characters
          </button>
          <button className="button primary" onClick={handlePlan} disabled={!!loading}>
            <WandSparkles size={16} />
            Create Scene Plan
          </button>
        </div>

        {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}

        {resolveResult && (resolveResult.matches.length > 0 || resolveResult.possible_new_characters.length > 0) && (
          <div className="resolve-box">
            <div className="scene-title">Character resolution</div>
            <div className="small-list">
              {resolveResult.matches.map((match) => (
                <span className="tag" key={match.character_id}>
                  <CircleCheck size={12} />
                  {match.canonical_name} via {match.matched_alias}
                </span>
              ))}
              {resolveResult.possible_new_characters.map((name) => (
                <span className="tag" key={name}>new: {name}</span>
              ))}
            </div>
          </div>
        )}

        {episode && (
          <div style={{ marginTop: 18 }}>
            <div className="panel-title" style={{ fontSize: 16 }}>{episode.title}</div>
            <div className="panel-copy">{episode.continuity_notes}</div>
            <div className="scene-list" style={{ marginTop: 12 }}>
              {episode.scenes
                .slice()
                .sort((a, b) => a.scene_number - b.scene_number)
                .map((scene) => (
                  <article className="scene-card" key={scene.id}>
                    <div className="scene-title">
                      Scene {scene.scene_number} · {scene.intensity} · {scene.status}
                    </div>
                    <div className="scene-text">{scene.narration}</div>
                    <div className="form-text">
                      <strong>Background:</strong> {scene.background}
                    </div>
                  </article>
                ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

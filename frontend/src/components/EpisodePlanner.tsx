"use client";

import { BookMarked, CircleCheck, Image, Pencil, Save, ScanSearch, WandSparkles, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  batchUpdateScenes,
  createEpisodePlan,
  Episode,
  EpisodeScene,
  listEpisodes,
  resolveCharacters,
  ResolveResponse,
  updateEpisodeStatus,
  updateScene,
} from "@/lib/api";
import type { SelectedSource } from "@/components/StudioWorkspace";

const SAMPLE = "Krishna and Balarama enter Vrindavan with the cowherd boys. Mother Yashoda watches with love as Krishna plays his flute near the Yamuna. A demon appears and Krishna protects everyone with divine grace.";

export function EpisodePlanner({
  selectedSources,
  onClearSources,
}: {
  selectedSources: SelectedSource[];
  onClearSources: () => void;
}) {
  const [text, setText] = useState(SAMPLE);
  const [sceneCount, setSceneCount] = useState(8);
  const [resolveResult, setResolveResult] = useState<ResolveResponse | null>(null);
  const [episode, setEpisode] = useState<Episode | null>(null);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editingSceneId, setEditingSceneId] = useState<string | null>(null);
  const [selectedSceneIds, setSelectedSceneIds] = useState<string[]>([]);
  const [batchInstruction, setBatchInstruction] = useState("");
  const [generationMode, setGenerationMode] = useState("grok");
  const [draftScene, setDraftScene] = useState<Pick<EpisodeScene, "narration" | "background" | "intensity" | "image_prompt" | "status"> | null>(null);

  const sourceRefs = useMemo(() => selectedSources.map((source) => source.ref), [selectedSources]);

  useEffect(() => {
    if (selectedSources.length === 0) return;
    setText(selectedSources.map(sourceToStoryDirection).join("\n\n"));
  }, [selectedSources]);

  useEffect(() => {
    refreshEpisodes();
  }, []);

  async function refreshEpisodes() {
    try {
      setEpisodes(await listEpisodes());
    } catch {
      // Episode history is helpful, but it should not block planning.
    }
  }

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
      const next = await createEpisodePlan(text, sceneCount, sourceRefs, generationMode);
      setEpisode(next);
      setSelectedSceneIds([]);
      setResolveResult({
        matches: [],
        possible_new_characters: [],
      });
      await refreshEpisodes();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Planning failed");
    } finally {
      setLoading(null);
    }
  }

  function startEdit(scene: EpisodeScene) {
    setEditingSceneId(scene.id);
    setDraftScene({
      narration: scene.narration,
      background: scene.background,
      intensity: scene.intensity,
      image_prompt: scene.image_prompt,
      status: scene.status,
    });
  }

  function cancelEdit() {
    setEditingSceneId(null);
    setDraftScene(null);
  }

  async function saveScene(sceneId: string) {
    if (!draftScene || !episode) return;
    setLoading(`scene-${sceneId}`);
    setError(null);
    try {
      const saved = await updateScene(sceneId, draftScene);
      setEpisode({
        ...episode,
        scenes: episode.scenes.map((scene) => (scene.id === sceneId ? saved : scene)),
      });
      cancelEdit();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scene update failed");
    } finally {
      setLoading(null);
    }
  }

  async function saveBatch() {
    if (!episode || selectedSceneIds.length === 0) return;
    setLoading("batch");
    setError(null);
    try {
      const savedScenes = await batchUpdateScenes({
        scene_ids: selectedSceneIds,
        narration_instruction: batchInstruction || undefined,
        status: "needs_revision",
      });
      const byId = new Map(savedScenes.map((scene) => [scene.id, scene]));
      setEpisode({
        ...episode,
        scenes: episode.scenes.map((scene) => byId.get(scene.id) || scene),
      });
      setBatchInstruction("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Batch update failed");
    } finally {
      setLoading(null);
    }
  }

  async function setEpisodeStatus(status: string) {
    if (!episode) return;
    setLoading("episode-status");
    setError(null);
    try {
      const saved = await updateEpisodeStatus(episode.id, status);
      setEpisode(saved);
      await refreshEpisodes();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Episode status update failed");
    } finally {
      setLoading(null);
    }
  }

  function toggleScene(sceneId: string) {
    setSelectedSceneIds((current) =>
      current.includes(sceneId) ? current.filter((id) => id !== sceneId) : [...current, sceneId],
    );
  }

  function updateDraft(field: keyof NonNullable<typeof draftScene>, value: string) {
    setDraftScene((current) => (current ? { ...current, [field]: value } : current));
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
            Start from a scripture reference or a custom plot. Story text is drafted in English; Tatparya references stay attached as accuracy context.
          </div>
          <div className="planner-note">
            Scene plans are generated on the fly. Grok is the production story engine; the fast deterministic draft is available for offline fallback and testing.
          </div>
        </div>
      </div>
      <div className="panel-body">
        <div className="field">
          <label htmlFor="plot">Story direction (English default)</label>
          <textarea
            id="plot"
            className="textarea"
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
        </div>
        {selectedSources.length > 0 && (
          <div className="resolve-box">
            <div className="scene-title">Selected repository sources</div>
            <div className="small-list">
              {selectedSources.map((source) => (
                <span className="tag" key={source.ref}>{source.ref}</span>
              ))}
            </div>
            <button className="button" style={{ marginTop: 10 }} onClick={onClearSources}>
              Clear Sources
            </button>
          </div>
        )}
        <div className="field">
          <label htmlFor="scene-count">Target scenes</label>
          <div className="planner-controls-grid">
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
            <select
              className="select"
              value={generationMode}
              onChange={(event) => setGenerationMode(event.target.value)}
              aria-label="Generation engine"
            >
              <option value="grok">Grok story engine</option>
              <option value="draft">Fast deterministic draft</option>
            </select>
          </div>
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

        {episodes.length > 0 && (
          <div className="episode-library">
            <div className="scene-title">Episode library</div>
            <div className="episode-library-list">
              {episodes.slice(0, 8).map((item) => (
                <button className="episode-row" key={item.id} type="button" onClick={() => setEpisode(item)}>
                  <span>{item.title}</span>
                  <small>{item.status} · {item.scenes.length} scenes</small>
                </button>
              ))}
            </div>
          </div>
        )}

        {episode && (
          <div style={{ marginTop: 18 }}>
            <div className="episode-heading">
              <div>
                <div className="panel-title" style={{ fontSize: 16 }}>{episode.title}</div>
                <div className="panel-copy">{episode.continuity_notes}</div>
              </div>
              <select
                className="select compact-select"
                value={episode.status}
                onChange={(event) => setEpisodeStatus(event.target.value)}
                disabled={!!loading}
                aria-label="Episode status"
              >
                <option value="draft">draft</option>
                <option value="in_review">in review</option>
                <option value="approved">approved</option>
                <option value="archived">archived</option>
              </select>
            </div>
            <div className="batch-editor">
              <div className="scene-title">{selectedSceneIds.length} selected for group edit</div>
              <div className="batch-editor-row">
                <input
                  className="input"
                  placeholder="Revision direction for selected scenes..."
                  value={batchInstruction}
                  onChange={(event) => setBatchInstruction(event.target.value)}
                />
                <button className="button" type="button" onClick={saveBatch} disabled={loading === "batch" || selectedSceneIds.length === 0}>
                  Apply to Selected
                </button>
              </div>
            </div>
            <div className="scene-list" style={{ marginTop: 12 }}>
              {episode.scenes
                .slice()
                .sort((a, b) => a.scene_number - b.scene_number)
                .map((scene) => (
                  <article className="scene-card" key={scene.id}>
                    <div className="scene-card-header">
                      <div className="scene-title scene-select-title">
                        <input
                          type="checkbox"
                          checked={selectedSceneIds.includes(scene.id)}
                          onChange={() => toggleScene(scene.id)}
                          aria-label={`Select scene ${scene.scene_number}`}
                        />
                        <span>Scene {scene.scene_number} · {scene.intensity} · {scene.status}</span>
                      </div>
                      {editingSceneId === scene.id ? (
                        <div className="scene-actions">
                          <button
                            className="icon-button"
                            aria-label={`Save scene ${scene.scene_number}`}
                            title="Save scene"
                            onClick={() => saveScene(scene.id)}
                            disabled={loading === `scene-${scene.id}`}
                          >
                            <Save size={15} />
                          </button>
                          <button
                            className="icon-button"
                            aria-label={`Cancel editing scene ${scene.scene_number}`}
                            title="Cancel"
                            onClick={cancelEdit}
                            disabled={loading === `scene-${scene.id}`}
                          >
                            <X size={15} />
                          </button>
                        </div>
                      ) : (
                        <button
                          className="icon-button"
                          aria-label={`Edit scene ${scene.scene_number}`}
                          title="Edit scene"
                          onClick={() => startEdit(scene)}
                        >
                          <Pencil size={15} />
                        </button>
                      )}
                    </div>
                    {editingSceneId === scene.id && draftScene ? (
                      <div className="scene-editor">
                        <div className="field">
                          <label htmlFor={`scene-${scene.id}-narration`}>Narration</label>
                          <textarea
                            id={`scene-${scene.id}-narration`}
                            className="textarea compact"
                            value={draftScene.narration}
                            onChange={(event) => updateDraft("narration", event.target.value)}
                          />
                        </div>
                        <div className="field">
                          <label htmlFor={`scene-${scene.id}-background`}>Background</label>
                          <textarea
                            id={`scene-${scene.id}-background`}
                            className="textarea compact"
                            value={draftScene.background}
                            onChange={(event) => updateDraft("background", event.target.value)}
                          />
                        </div>
                        <div className="scene-edit-grid">
                          <div className="field">
                            <label htmlFor={`scene-${scene.id}-intensity`}>Intensity</label>
                            <select
                              id={`scene-${scene.id}-intensity`}
                              className="select"
                              value={draftScene.intensity}
                              onChange={(event) => updateDraft("intensity", event.target.value)}
                            >
                              <option value="peaceful">peaceful</option>
                              <option value="tense">tense</option>
                              <option value="divine_victory">divine_victory</option>
                            </select>
                          </div>
                          <div className="field">
                            <label htmlFor={`scene-${scene.id}-status`}>Status</label>
                            <select
                              id={`scene-${scene.id}-status`}
                              className="select"
                              value={draftScene.status}
                              onChange={(event) => updateDraft("status", event.target.value)}
                            >
                              <option value="draft">draft</option>
                              <option value="approved">approved</option>
                              <option value="needs_revision">needs_revision</option>
                            </select>
                          </div>
                        </div>
                        <div className="field">
                          <label htmlFor={`scene-${scene.id}-prompt`}>Image prompt / visual direction</label>
                          <textarea
                            id={`scene-${scene.id}-prompt`}
                            className="textarea compact"
                            value={draftScene.image_prompt}
                            onChange={(event) => updateDraft("image_prompt", event.target.value)}
                          />
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="scene-text">{scene.narration}</div>
                        <div className="form-text">
                          <strong>Background:</strong> {scene.background}
                        </div>
                      </>
                    )}
                    {scene.image_brief && (
                      <details className="image-brief">
                        <summary>
                          <Image size={15} />
                          Scene image brief
                        </summary>
                        <div className="brief-block">
                          <div className="brief-label">Scene description</div>
                          <div className="scene-text">{scene.image_brief.scene_description}</div>
                        </div>
                        <div className="brief-block">
                          <div className="brief-label">Source references</div>
                          <div className="small-list">
                            {(scene.image_brief.source_refs.length ? scene.image_brief.source_refs : scene.source_refs).map((ref) => (
                              <span className="tag" key={ref}>{ref}</span>
                            ))}
                          </div>
                        </div>
                        <div className="brief-block">
                          <div className="brief-label">Characters and references</div>
                          <div className="brief-character-list">
                            {scene.image_brief.characters.map((character) => (
                              <div className="brief-character" key={character.character_id}>
                                <div className="character-name">{character.canonical_name}</div>
                                <div className="form-text">
                                  {character.form_name || "Default form"} · {character.reference_status.replaceAll("_", " ")}
                                </div>
                                <div className="form-text">{character.visual_profile}</div>
                                {character.cultural_rules && (
                                  <div className="form-text">
                                    <strong>Cultural rules:</strong> {character.cultural_rules}
                                  </div>
                                )}
                                <div className="small-list">
                                  {character.reference_assets.length > 0 ? (
                                    character.reference_assets.map((asset) => (
                                      <span className="tag" key={asset.id}>
                                        approved {asset.asset_type} v{asset.version}
                                      </span>
                                    ))
                                  ) : (
                                    <span className="tag">no approved image yet</span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                        <div className="brief-block">
                          <div className="brief-label">Continuity context</div>
                          {scene.image_brief.previous_scene_context.length > 0 ? (
                            scene.image_brief.previous_scene_context.map((context) => (
                              <div className="form-text" key={context}>{context}</div>
                            ))
                          ) : (
                            <div className="form-text">First scene in this episode; use approved character references and source refs as the anchor.</div>
                          )}
                        </div>
                        <div className="brief-block">
                          <div className="brief-label">Generation requirements</div>
                          <div className="brief-requirements">
                            {scene.image_brief.reference_requirements.map((requirement) => (
                              <span className="tag" key={requirement}>{requirement}</span>
                            ))}
                          </div>
                        </div>
                        <div className="brief-block">
                          <div className="brief-label">Full image prompt</div>
                          <div className="prompt-box">{scene.image_brief.image_prompt}</div>
                        </div>
                      </details>
                    )}
                  </article>
                ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function sourceToStoryDirection(source: SelectedSource): string {
  const premise = source.text
    .split("\n")
    .map((line) => line.trim())
    .find((line) => line.toLowerCase().startsWith("story premise:"));

  if (premise) {
    return premise.split(":", 2)[1]?.trim() || premise;
  }

  return `Create an English Bhagavatham episode from ${source.ref}.`;
}

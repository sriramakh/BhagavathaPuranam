export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CharacterAsset {
  id: string;
  form_id: string;
  asset_type: string;
  path: string;
  provider: string;
  version: number;
  approved: boolean;
  url?: string | null;
}

export interface CharacterForm {
  id: string;
  character_id: string;
  form_name: string;
  age_stage: string;
  visual_profile: string;
  cultural_rules: string;
  negative_prompt: string;
  status: string;
  is_default: boolean;
  assets: CharacterAsset[];
}

export interface Character {
  id: string;
  canonical_name: string;
  category: string;
  description: string;
  source_notes: string;
  status: string;
  aliases: { id: string; alias: string; confidence: number; notes: string }[];
  forms: CharacterForm[];
}

export interface ResolveResponse {
  matches: {
    character_id: string;
    canonical_name: string;
    matched_alias: string;
    confidence: number;
  }[];
  possible_new_characters: string[];
}

export interface SceneCharacterAsset {
  id: string;
  asset_type: string;
  provider: string;
  version: number;
  approved: boolean;
  url: string;
}

export interface SceneCharacterBrief {
  character_id: string;
  canonical_name: string;
  category: string;
  form_id?: string | null;
  form_name: string;
  visual_profile: string;
  cultural_rules: string;
  negative_prompt: string;
  reference_status: string;
  reference_assets: SceneCharacterAsset[];
}

export interface SceneImageBrief {
  source_refs: string[];
  scene_description: string;
  background: string;
  intensity: string;
  characters: SceneCharacterBrief[];
  previous_scene_context: string[];
  reference_requirements: string[];
  image_prompt: string;
}

export interface EpisodeScene {
  id: string;
  source_refs: string[];
  scene_number: number;
  narration: string;
  background: string;
  character_ids: string[];
  intensity: string;
  image_prompt: string;
  status: string;
  image_brief?: SceneImageBrief | null;
}

export interface Episode {
  id: string;
  title: string;
  source_mode: string;
  input_text: string;
  source_refs: string[];
  status: string;
  continuity_notes: string;
  scenes: EpisodeScene[];
}

export interface Shloka {
  id: string;
  canto: number;
  chapter: number;
  verse: string;
  sanskrit: string;
  transliteration: string;
  translation: string;
  summary: string;
  characters: string[];
  location: string;
  themes: string[];
  source_name: string;
  source_url: string;
  license: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export function listCharacters() {
  return request<Character[]>("/api/v1/characters");
}

export function resolveCharacters(text: string) {
  return request<ResolveResponse>("/api/v1/characters/resolve", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function listShlokas(params: { q?: string; canto?: number; chapter?: number } = {}) {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.canto) search.set("canto", String(params.canto));
  if (params.chapter) search.set("chapter", String(params.chapter));
  const query = search.toString();
  return request<Shloka[]>(`/api/v1/corpus/shlokas${query ? `?${query}` : ""}`);
}

export function createEpisodePlan(input_text: string, target_scene_count?: number, source_refs: string[] = []) {
  return request<Episode>("/api/v1/episodes/plan", {
    method: "POST",
    body: JSON.stringify({
      input_text,
      source_mode: "plot",
      source_refs,
      target_scene_count,
    }),
  });
}

export function updateScene(
  sceneId: string,
  payload: Partial<Pick<EpisodeScene, "narration" | "background" | "character_ids" | "intensity" | "image_prompt" | "status">>,
) {
  return request<EpisodeScene>(`/api/v1/episodes/scenes/${sceneId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function assetUrl(asset: CharacterAsset) {
  return `${API_URL}${asset.url || `/api/v1/assets/${asset.id}`}`;
}

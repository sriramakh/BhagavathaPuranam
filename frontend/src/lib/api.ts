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

export interface EpisodeScene {
  id: string;
  scene_number: number;
  narration: string;
  background: string;
  character_ids: string[];
  intensity: string;
  image_prompt: string;
  status: string;
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

export function createEpisodePlan(input_text: string, target_scene_count?: number) {
  return request<Episode>("/api/v1/episodes/plan", {
    method: "POST",
    body: JSON.stringify({
      input_text,
      source_mode: "plot",
      source_refs: [],
      target_scene_count,
    }),
  });
}

export function assetUrl(asset: CharacterAsset) {
  return `${API_URL}${asset.url || `/api/v1/assets/${asset.id}`}`;
}

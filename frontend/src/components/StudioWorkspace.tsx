"use client";

import { useState } from "react";
import { CharacterRegistry } from "@/components/CharacterRegistry";
import { CorpusBrowser } from "@/components/CorpusBrowser";
import { EpisodePlanner } from "@/components/EpisodePlanner";

export interface SelectedSource {
  ref: string;
  text: string;
}

export function StudioWorkspace() {
  const [selectedSources, setSelectedSources] = useState<SelectedSource[]>([]);

  function addSource(source: SelectedSource) {
    setSelectedSources((prev) =>
      prev.some((item) => item.ref === source.ref) ? prev : [...prev, source]
    );
  }

  function clearSources() {
    setSelectedSources([]);
  }

  return (
    <main className="studio-layout">
      <CorpusBrowser onUseSource={addSource} />
      <CharacterRegistry />
      <EpisodePlanner selectedSources={selectedSources} onClearSources={clearSources} />
    </main>
  );
}

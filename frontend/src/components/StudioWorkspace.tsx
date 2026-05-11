"use client";

import { BookMarked, Library, UserRoundCheck } from "lucide-react";
import { useState } from "react";
import { CharacterRegistry } from "@/components/CharacterRegistry";
import { CorpusBrowser } from "@/components/CorpusBrowser";
import { EpisodePlanner } from "@/components/EpisodePlanner";

export interface SelectedSource {
  ref: string;
  text: string;
}

type WorkspaceTab = "sources" | "characters" | "episode";

export function StudioWorkspace() {
  const [selectedSources, setSelectedSources] = useState<SelectedSource[]>([]);
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("sources");

  function addSource(source: SelectedSource) {
    setSelectedSources((prev) =>
      prev.some((item) => item.ref === source.ref) ? prev : [...prev, source]
    );
    setActiveTab("episode");
  }

  function clearSources() {
    setSelectedSources([]);
  }

  return (
    <main className="studio-layout">
      <div className="workspace-frame">
        <div className="workspace-nav" role="tablist" aria-label="Studio workflow">
          <button
            className={`workspace-tab ${activeTab === "sources" ? "active" : ""}`}
            type="button"
            role="tab"
            aria-selected={activeTab === "sources"}
            onClick={() => setActiveTab("sources")}
          >
            <Library size={16} />
            Sources
          </button>
          <button
            className={`workspace-tab ${activeTab === "characters" ? "active" : ""}`}
            type="button"
            role="tab"
            aria-selected={activeTab === "characters"}
            onClick={() => setActiveTab("characters")}
          >
            <UserRoundCheck size={16} />
            Characters
          </button>
          <button
            className={`workspace-tab ${activeTab === "episode" ? "active" : ""}`}
            type="button"
            role="tab"
            aria-selected={activeTab === "episode"}
            onClick={() => setActiveTab("episode")}
          >
            <BookMarked size={16} />
            Episode
            {selectedSources.length > 0 && <span>{selectedSources.length}</span>}
          </button>
        </div>

        <div className={`workspace-panel ${activeTab === "sources" ? "active" : ""}`}>
          <CorpusBrowser onUseSource={addSource} />
        </div>
        <div className={`workspace-panel ${activeTab === "characters" ? "active" : ""}`}>
          <CharacterRegistry />
        </div>
        <div className={`workspace-panel ${activeTab === "episode" ? "active" : ""}`}>
          <EpisodePlanner selectedSources={selectedSources} onClearSources={clearSources} />
        </div>
      </div>
    </main>
  );
}

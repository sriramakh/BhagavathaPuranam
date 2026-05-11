import { BookOpenCheck, Database, ShieldCheck } from "lucide-react";
import { StudioWorkspace } from "@/components/StudioWorkspace";

export default function Home() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <div className="brand-mark" />
            <div>
              <div className="brand-title">Bhagavatha Puranam Studio</div>
              <div className="brand-subtitle">Character memory, shloka-aware episodes, devotional visual continuity</div>
            </div>
          </div>
          <div className="toolbar">
            <span className="status-pill">
              <Database size={15} />
              memory-first
            </span>
            <span className="status-pill">
              <ShieldCheck size={15} />
              mythology mode
            </span>
            <span className="status-pill">
              <BookOpenCheck size={15} />
              scene approval
            </span>
          </div>
        </div>
      </header>

      <StudioWorkspace />
    </div>
  );
}

export type LayoutMode = "chat" | "sidebar" | "popup";

const MODES: { id: LayoutMode; label: string }[] = [
  { id: "chat", label: "CopilotChat" },
  { id: "sidebar", label: "CopilotSidebar" },
  { id: "popup", label: "CopilotPopup" },
];

interface LayoutModeSwitcherProps {
  mode: LayoutMode;
  onChange: (mode: LayoutMode) => void;
}

export function LayoutModeSwitcher({ mode, onChange }: LayoutModeSwitcherProps) {
  return (
    <div className="layout-switcher">
      <span className="layout-switcher-label">布局</span>
      {MODES.map(({ id, label }) => (
        <button
          key={id}
          type="button"
          onClick={() => onChange(id)}
          className={`layout-btn${mode === id ? " active" : ""}`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

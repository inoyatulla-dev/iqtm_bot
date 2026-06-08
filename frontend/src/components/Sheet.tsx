import type { ReactNode } from "react";

interface SheetProps {
  title?: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
}

export function Sheet({ title, subtitle, onClose, children }: SheetProps) {
  return (
    <div className="sheet-overlay" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <div className="sheet__handle" />
        {title && (
          <div className="sheet__title">
            {title}
            {subtitle && <div className="sheet__subtitle">{subtitle}</div>}
          </div>
        )}
        {children}
      </div>
    </div>
  );
}

interface ActionRowProps {
  icon: string;
  label: string;
  danger?: boolean;
  checked?: boolean;
  onClick: () => void;
}

export function ActionRow({ icon, label, danger, checked, onClick }: ActionRowProps) {
  return (
    <button className={`action-row${danger ? " danger" : ""}`} onClick={onClick}>
      <span className="action-row__icon">{icon}</span>
      <span>{label}</span>
      {checked && <span className="check">✓</span>}
    </button>
  );
}

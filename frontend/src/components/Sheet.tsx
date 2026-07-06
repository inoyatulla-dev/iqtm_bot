import type { ReactNode } from "react";
import { Check, X } from "lucide-react";

interface SheetProps {
  title?: ReactNode;
  subtitle?: ReactNode;
  /** Sarlavha ostida, skroll qilinganda ham ko'rinib turadigan asosiy amal (masalan "Tahrirlash") */
  stickyAction?: ReactNode;
  onClose: () => void;
  children: ReactNode;
}

export function Sheet({ title, subtitle, stickyAction, onClose, children }: SheetProps) {
  return (
    <div className="sheet-overlay">
      <div className="sheet">
        <div className="sheet__top">
          <div className="sheet__handle" />
          <button className="sheet__close" onClick={onClose} aria-label="Yopish">
            <X size={16} />
          </button>
          {title && (
            <div className="sheet__title">
              {title}
              {subtitle && <div className="sheet__subtitle">{subtitle}</div>}
            </div>
          )}
          {stickyAction && <div className="sheet__sticky-action">{stickyAction}</div>}
        </div>
        {children}
      </div>
    </div>
  );
}

interface ActionRowProps {
  icon: ReactNode;
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
      {checked && <span className="check"><Check size={18} /></span>}
    </button>
  );
}

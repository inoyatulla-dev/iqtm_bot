import { Bell } from "lucide-react";
import { useI18n } from "../i18n";

interface Props {
  unread: number;
  onClick: () => void;
}

export function NotificationBell({ unread, onClick }: Props) {
  const { t } = useI18n();
  return (
    <button type="button" className="notif-bell__btn" onClick={onClick} aria-label={t("notif.title")}>
      <Bell size={20} />
      {unread > 0 && <span className="notif-bell__badge">{unread > 9 ? "9+" : unread}</span>}
    </button>
  );
}

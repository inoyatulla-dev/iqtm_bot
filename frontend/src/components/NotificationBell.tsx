import { useEffect, useRef, useState } from "react";
import { Bell } from "lucide-react";
import { notificationsApi } from "../api/client";
import type { AppNotification } from "../api/types";
import { useI18n } from "../i18n";

const POLL_MS = 30000;

interface Props {
  onOpenTask: (taskId: number) => void;
}

export function NotificationBell({ onOpenTask }: Props) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<AppNotification[]>([]);
  const [unread, setUnread] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  async function refreshUnread() {
    try {
      setUnread(await notificationsApi.unreadCount());
    } catch {
      /* jim */
    }
  }

  useEffect(() => {
    refreshUnread();
    const id = setInterval(refreshUnread, POLL_MS);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (!open) return;
    notificationsApi.list().then(setItems).catch(() => {});
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  async function handleClick(n: AppNotification) {
    if (!n.is_read) {
      setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)));
      setUnread((c) => Math.max(0, c - 1));
      notificationsApi.markRead(n.id).catch(() => {});
    }
    setOpen(false);
    if (n.task_id) onOpenTask(n.task_id);
  }

  async function handleMarkAll() {
    setItems((prev) => prev.map((x) => ({ ...x, is_read: true })));
    setUnread(0);
    try {
      await notificationsApi.markAllRead();
    } catch {
      /* jim */
    }
  }

  function stripHtml(s: string): string {
    return s.replace(/<[^>]+>/g, "");
  }

  return (
    <div className="notif-bell" ref={ref}>
      <button
        type="button"
        className="notif-bell__btn"
        onClick={() => setOpen((v) => !v)}
        aria-label={t("notif.title")}
      >
        <Bell size={20} />
        {unread > 0 && <span className="notif-bell__badge">{unread > 9 ? "9+" : unread}</span>}
      </button>
      {open && (
        <div className="notif-bell__panel">
          <div className="notif-bell__head">
            <span>{t("notif.title")}</span>
            {unread > 0 && (
              <button type="button" className="notif-bell__markall" onClick={handleMarkAll}>
                {t("notif.markAll")}
              </button>
            )}
          </div>
          <div className="notif-bell__list">
            {items.length === 0 && <div className="notif-bell__empty">{t("notif.empty")}</div>}
            {items.map((n) => (
              <button
                type="button"
                key={n.id}
                className={`notif-bell__item${n.is_read ? "" : " unread"}`}
                onClick={() => handleClick(n)}
              >
                <div className="notif-bell__text">{stripHtml(n.text)}</div>
                <div className="notif-bell__time">
                  {new Date(n.created_at).toLocaleString()}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

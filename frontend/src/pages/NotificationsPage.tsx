import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle, ArrowLeft, CheckCircle2, ClipboardList, Eye, MessageSquare,
  RefreshCw, Archive as ArchiveIcon, Bell,
} from "lucide-react";
import { notificationsApi } from "../api/client";
import type { AppNotification } from "../api/types";
import { useI18n } from "../i18n";
import { formatTimeAgo } from "../utils/datetime";
import "../components/tasks/tasks.css";
import "./notifications.css";

type MainTab = "incoming" | "archive";
type TypeFilter = "all" | "task" | "comment";

const PAGE_SIZES = [6, 10, 20, 50];

const TYPE_META: Record<string, { title: string; icon: typeof Bell; cls: string }> = {
  task_assigned: { title: "Yangi vazifa tayinlandi", icon: ClipboardList, cls: "accent" },
  status_change: { title: "Vazifa holati o'zgardi", icon: RefreshCw, cls: "accent" },
  done: { title: "Vazifa tasdiqlandi", icon: CheckCircle2, cls: "ok" },
  comment: { title: "Yangi izoh", icon: MessageSquare, cls: "accent2" },
  reminder: { title: "Vazifa muddati yaqinlashmoqda", icon: AlertTriangle, cls: "danger" },
};
const DEFAULT_META = { title: "Bildirishnoma", icon: Bell, cls: "accent" };

function typeBucket(type: string): Exclude<TypeFilter, "all"> {
  return type === "comment" ? "comment" : "task";
}

function stripHtml(s: string): string {
  return s.replace(/<[^>]+>/g, "");
}

interface Props {
  onOpenTask: (taskId: number) => void;
  onBack: () => void;
  onChanged: () => void;
}

export function NotificationsPage({ onOpenTask, onBack, onChanged }: Props) {
  const { lang } = useI18n();
  const [items, setItems] = useState<AppNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [mainTab, setMainTab] = useState<MainTab>("incoming");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(6);

  useEffect(() => {
    notificationsApi.list().then(setItems).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setPage(1);
  }, [mainTab, typeFilter, pageSize]);

  const unreadCount = useMemo(() => items.filter((n) => !n.is_read).length, [items]);

  const filtered = useMemo(
    () =>
      items
        .filter((n) => (mainTab === "incoming" ? !n.is_archived : n.is_archived))
        .filter((n) => typeFilter === "all" || typeBucket(n.type) === typeFilter),
    [items, mainTab, typeFilter]
  );

  const total = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const clampedPage = Math.min(page, totalPages);
  const startIdx = (clampedPage - 1) * pageSize;
  const pageItems = filtered.slice(startIdx, startIdx + pageSize);
  const rangeStart = total === 0 ? 0 : startIdx + 1;
  const rangeEnd = Math.min(startIdx + pageSize, total);

  async function view(n: AppNotification) {
    if (!n.is_read) {
      setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)));
      notificationsApi.markRead(n.id).then(onChanged).catch(() => {});
    }
    if (n.task_id) onOpenTask(n.task_id);
  }

  async function archive(n: AppNotification) {
    setItems((prev) =>
      prev.map((x) => (x.id === n.id ? { ...x, is_archived: true, is_read: true } : x))
    );
    try {
      await notificationsApi.archive(n.id);
    } finally {
      onChanged();
    }
  }

  async function markAllRead() {
    setItems((prev) => prev.map((x) => ({ ...x, is_read: true })));
    try {
      await notificationsApi.markAllRead();
    } finally {
      onChanged();
    }
  }

  if (loading) {
    return <div className="center-screen">Yuklanmoqda…</div>;
  }

  return (
    <div className="tasks-page">
      <div className="tasks-head">
        <div className="tasks-head__title">
          <button type="button" className="notif-page__back" onClick={onBack}>
            <ArrowLeft size={16} /> Orqaga
          </button>
          <h1>Bildirishnomalar</h1>
          <p>{unreadCount} ta o'qilmagan</p>
        </div>
        <div className="tasks-head__actions">
          <div className="view-tabs">
            <button
              type="button"
              className={`view-tab${mainTab === "incoming" ? " active" : ""}`}
              onClick={() => setMainTab("incoming")}
            >
              Kelganlar
            </button>
            <button
              type="button"
              className={`view-tab${mainTab === "archive" ? " active" : ""}`}
              onClick={() => setMainTab("archive")}
            >
              Arxiv
            </button>
          </div>
          {unreadCount > 0 && (
            <button type="button" className="btn btn--ghost btn--sm" onClick={markAllRead}>
              Barchasini o'qilgan qilish
            </button>
          )}
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-item">
          <span className="filter-label">Tur:</span>
          <div className="quick-chips">
            {(
              [
                ["all", "Hammasi"],
                ["task", "Vazifa"],
                ["comment", "Izoh"],
              ] as [TypeFilter, string][]
            ).map(([key, label]) => (
              <button
                key={key}
                type="button"
                className={`quick-chip${typeFilter === key ? " active" : ""}`}
                onClick={() => setTypeFilter(key)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="tasks-panel">
        {pageItems.length === 0 && (
          <div className="notif-page__empty">
            {mainTab === "incoming" ? "Bildirishnomalar yo'q" : "Arxiv bo'sh"}
          </div>
        )}
        {pageItems.map((n) => {
          const meta = TYPE_META[n.type] ?? DEFAULT_META;
          const Icon = meta.icon;
          return (
            <div className="notif-item" key={n.id}>
              <div className={`notif-item__icon notif-item__icon--${meta.cls}`}>
                <Icon size={18} />
              </div>
              <div className="notif-item__body">
                <div className="notif-item__title-row">
                  <span className="notif-item__title">{meta.title}</span>
                  {!n.is_read && <span className="notif-item__dot" />}
                </div>
                <div className="notif-item__text">{stripHtml(n.text)}</div>
                <div className="notif-item__time">{formatTimeAgo(n.created_at, lang)}</div>
              </div>
              <div className="notif-item__actions">
                <button type="button" className="btn btn--ghost btn--sm" onClick={() => view(n)}>
                  <Eye size={14} /> Ko'rish
                </button>
                {mainTab === "incoming" && (
                  <button
                    type="button"
                    className="btn btn--ghost btn--sm"
                    onClick={() => archive(n)}
                  >
                    <ArchiveIcon size={14} /> Arxivlash
                  </button>
                )}
              </div>
            </div>
          );
        })}

        {total > 0 && (
          <div className="notif-pager">
            <span className="notif-pager__info">
              {rangeStart}-{rangeEnd} / {total}
            </span>
            <div className="notif-pager__size">
              <span>Sahifada:</span>
              <select
                className="filter-control"
                value={pageSize}
                onChange={(e) => setPageSize(Number(e.target.value))}
              >
                {PAGE_SIZES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div className="notif-pager__pages">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  type="button"
                  className={`notif-pager__page${p === clampedPage ? " active" : ""}`}
                  onClick={() => setPage(p)}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

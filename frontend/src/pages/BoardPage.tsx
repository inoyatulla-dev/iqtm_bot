import { useEffect, useMemo, useState } from "react";
import {
  DndContext, DragEndEvent, PointerSensor, useSensor, useSensors,
} from "@dnd-kit/core";
import { Archive, ArrowDownUp, LayoutGrid, List, Plus, X } from "lucide-react";
import { tasksApi } from "../api/client";
import type { Task } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";
import { haptic } from "../telegram";
import { useIsMobile } from "../hooks/useIsMobile";
import { Column } from "../components/board/Column";
import { TaskCard } from "../components/board/TaskCard";
import { DateFilter, ALL_TIME, type DateRange } from "../components/tasks/DateFilter";
import { TasksTable } from "../components/tasks/TasksTable";
import { MobileTaskList } from "../components/tasks/MobileTaskList";
import { TaskForm } from "./TaskForm";
import "../components/tasks/tasks.css";

type View = "board" | "list" | "archive";
type QuickFilter = "all" | "mine" | "today" | "overdue" | "in_progress" | "done";
type SortField = "created_at" | "updated_at" | "deadline" | "done_at";
type SortDir = "asc" | "desc";

const QUICK_FILTERS: { key: QuickFilter; label: string }[] = [
  { key: "all", label: "Hammasi" },
  { key: "mine", label: "Mening vazifalarim" },
  { key: "today", label: "Bugun" },
  { key: "overdue", label: "Kechikkan" },
  { key: "in_progress", label: "Jarayonda" },
  { key: "done", label: "Bajarilgan" },
];

const SORT_FIELD_LABELS: Record<Exclude<SortField, "done_at">, string> = {
  created_at: "Yaratilgan sana",
  updated_at: "Yangilangan sana",
  deadline: "Muddat",
};

function todayIso(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** Berilgan maydon bo'yicha tartiblaydi; qiymati yo'q vazifalar oxirida qoladi. */
function sortTasks(list: Task[], field: SortField, dir: SortDir): Task[] {
  const withVal = list.filter((t) => t[field]);
  const withoutVal = list.filter((t) => !t[field]);
  withVal.sort((a, b) => new Date(a[field] as string).getTime() - new Date(b[field] as string).getTime());
  if (dir === "desc") withVal.reverse();
  return [...withVal, ...withoutVal];
}

export function BoardPage() {
  const { deps, columns, isObserver, isBoss, user } = useAuth();
  const { t } = useI18n();
  const isMobile = useIsMobile();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Task | null>(null);
  const [autoConfirm, setAutoConfirm] = useState(false);

  const [view, setView] = useState<View>("board");
  const [range, setRange] = useState<DateRange>(ALL_TIME);
  const [empId, setEmpId] = useState<string>("all");
  const [statusKey, setStatusKey] = useState<string>("all");
  const [quickFilter, setQuickFilter] = useState<QuickFilter>("all");
  const [search, setSearch] = useState("");
  const [restoringId, setRestoringId] = useState<number | null>(null);
  const [sortField, setSortField] = useState<Exclude<SortField, "done_at">>("created_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [archiveDir, setArchiveDir] = useState<SortDir>("desc");

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } })
  );

  async function load() {
    setLoading(true);
    setTasks(await tasksApi.list());
    setLoading(false);
  }
  useEffect(() => {
    load();
  }, []);

  const doneKeys = useMemo(
    () => new Set(columns.filter((c) => c.is_done).map((c) => c.key)),
    [columns]
  );
  const inProgressCol = useMemo(
    () => columns.find((c) => c.key === "in_progress") || columns.find((c) => !c.is_initial && !c.is_done),
    [columns]
  );

  // Filtr uchun xodimlar ro'yxati — vazifalardagi noyob mas'ul va biriktirilganlardan
  const employees = useMemo(() => {
    const map = new Map<number, string>();
    for (const t of tasks) {
      if (t.masul_id && t.masul_name) map.set(t.masul_id, t.masul_name);
      for (const a of t.assignees || []) map.set(a.id, a.name);
    }
    return [...map.entries()].map(([id, name]) => ({ id, name })).sort((a, b) => a.name.localeCompare(b.name));
  }, [tasks]);

  function taskDate(t: Task): string | null {
    return t.deadline || t.created_at || null;
  }
  function inRange(t: Task): boolean {
    if (range.mode === "all") return true;
    const d = taskDate(t);
    if (!d) return false;
    const day = d.slice(0, 10);
    if (range.from && day < range.from) return false;
    if (range.to && day > range.to) return false;
    return true;
  }

  function matchesQuick(t: Task): boolean {
    switch (quickFilter) {
      case "mine":
        return (
          t.masul_id === user?.id ||
          t.created_by === user?.id ||
          !!t.assignees?.some((a) => a.id === user?.id)
        );
      case "today":
        return !!t.deadline && t.deadline.slice(0, 10) === todayIso();
      case "overdue":
        return t.is_overdue;
      case "in_progress":
        return !!inProgressCol && t.status === inProgressCol.key;
      case "done":
        return doneKeys.has(t.status);
      default:
        return true;
    }
  }

  function matches(t: Task): boolean {
    if (!inRange(t)) return false;
    if (
      empId !== "all" &&
      String(t.masul_id) !== empId &&
      !t.assignees?.some((a) => String(a.id) === empId)
    )
      return false;
    if (statusKey !== "all" && t.status !== statusKey) return false;
    if (!matchesQuick(t)) return false;
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      if (!t.name.toLowerCase().includes(q) && !(t.project_name || "").toLowerCase().includes(q))
        return false;
    }
    return true;
  }

  const filtered = useMemo(
    () => tasks.filter(matches),
    [tasks, range, empId, statusKey, quickFilter, search]
  );
  const activeCount = useMemo(() => tasks.filter((t) => !doneKeys.has(t.status)).length, [tasks, doneKeys]);

  // Arxivlangan (24 soatdan ortiq "bajarilgan" holatda turgan) vazifalar Doska/Ro'yxatdan
  // yashiriladi — faqat Arxiv bo'limida ko'rinadi.
  const activeTasks = useMemo(() => filtered.filter((t) => !t.is_archived), [filtered]);
  const boardTasks = useMemo(() => sortTasks(activeTasks, sortField, sortDir), [activeTasks, sortField, sortDir]);
  const listTasks = boardTasks;
  const archiveTasks = useMemo(
    () => sortTasks(filtered.filter((t) => t.is_archived), "done_at", archiveDir),
    [filtered, archiveDir]
  );

  const thisYear = new Date().getFullYear();
  const thisMonth = new Date().getMonth();
  const doneAll = tasks.filter((t) => t.is_archived);
  const doneYear = doneAll.filter((t) => { const d = t.done_at || taskDate(t); return d && new Date(d).getFullYear() === thisYear; });
  const doneMonth = doneYear.filter((t) => { const d = t.done_at || taskDate(t); return d && new Date(d).getMonth() === thisMonth; });

  const hasFilter = range.mode !== "all" || empId !== "all" || statusKey !== "all" || quickFilter !== "all" || !!search.trim();
  function clearFilters() {
    setRange(ALL_TIME);
    setEmpId("all");
    setStatusKey("all");
    setQuickFilter("all");
    setSearch("");
  }

  async function moveTask(taskId: number, newStatus: string) {
    if (isObserver) return;
    const task = tasks.find((x) => x.id === taskId);
    if (!task || task.status === newStatus) return;
    haptic();
    setTasks((prev) => prev.map((x) => (x.id === taskId ? { ...x, status: newStatus } : x)));
    try {
      const updated = await tasksApi.setStatus(taskId, newStatus);
      setTasks((prev) => prev.map((x) => (x.id === taskId ? updated : x)));
    } catch {
      load();
    }
  }

  async function onDragEnd(e: DragEndEvent) {
    const newStatus = e.over?.id as string | undefined;
    if (!newStatus) return;
    await moveTask(Number(e.active.id), newStatus);
  }

  async function restore(task: Task) {
    const initial = columns.find((c) => c.is_initial) || columns[0];
    if (!initial) return;
    setRestoringId(task.id);
    try {
      const updated = await tasksApi.setStatus(task.id, initial.key);
      setTasks((prev) => prev.map((x) => (x.id === task.id ? updated : x)));
    } catch {
      load();
    } finally {
      setRestoringId(null);
    }
  }

  async function deleteTask(task: Task) {
    if (!window.confirm(`"${task.name}" vazifasini o'chirishni tasdiqlaysizmi?`)) return;
    try {
      await tasksApi.remove(task.id);
      setTasks((prev) => prev.filter((x) => x.id !== task.id));
    } catch {
      load();
    }
  }

  function openTask(task: Task) {
    setEditing(task);
    setAutoConfirm(false);
    setFormOpen(true);
  }

  // Svayp: "Tayyor" — tasdiqlash + izoh ekraniga to'g'ridan-to'g'ri o'tadi
  function openConfirmDone(task: Task) {
    setEditing(task);
    setAutoConfirm(true);
    setFormOpen(true);
  }

  // Vazifa mazmunini kim tahrirlashi/o'chira olishi — backenddagi
  // can_edit_task / can_delete_task qoidasi bilan bir xil.
  function canEditTask(task: Task): boolean {
    if (isObserver) return false;
    if (isBoss) return true;
    return task.type === "personal" && task.created_by === user?.id;
  }

  if (loading) {
    return <div className="center-screen">{t("common.loading")}</div>;
  }

  return (
    <div className="tasks-page">
      {/* ── Sarlavha + ko'rinish tab'lari ── */}
      <div className="tasks-head">
        <div className="tasks-head__title">
          <h1>Vazifalar</h1>
          <p>{activeCount} ta faol vazifa</p>
        </div>
        <div className="tasks-head__actions">
          <div className="view-tabs">
            <button className={`view-tab${view === "board" ? " active" : ""}`} onClick={() => setView("board")}>
              <LayoutGrid size={15} /> <span>Doska</span>
            </button>
            <button className={`view-tab${view === "list" ? " active" : ""}`} onClick={() => setView("list")}>
              <List size={15} /> <span>Ro'yxat</span>
            </button>
            <button className={`view-tab${view === "archive" ? " active" : ""}`} onClick={() => setView("archive")}>
              <Archive size={15} /> <span>Arxiv</span>
            </button>
          </div>
          {!isObserver && (
            <button
              className="btn btn--primary btn--new"
              onClick={() => { setEditing(null); setAutoConfirm(false); setFormOpen(true); }}
            >
              <Plus size={16} /> Vazifa
            </button>
          )}
        </div>
      </div>

      {/* ── Filtr paneli (desktop / Doska & Arxiv mobil) ── */}
      {!(view === "list" && isMobile) && (
        <div className="filter-bar">
          <div className="filter-item">
            <span className="filter-label">Davr</span>
            <DateFilter value={range} onChange={setRange} />
          </div>
          <div className="filter-item">
            <span className="filter-label">Xodim</span>
            <select className="filter-control" value={empId} onChange={(e) => setEmpId(e.target.value)}>
              <option value="all">Barcha xodimlar</option>
              {employees.map((e) => (
                <option key={e.id} value={e.id}>{e.name}</option>
              ))}
            </select>
          </div>
          <div className="filter-item">
            <span className="filter-label">Holat</span>
            <select className="filter-control" value={statusKey} onChange={(e) => setStatusKey(e.target.value)}>
              <option value="all">Barcha holatlar</option>
              {columns.map((c) => (
                <option key={c.key} value={c.key}>{c.name}</option>
              ))}
            </select>
          </div>
          {(view === "board" || view === "list") && (
            <div className="filter-item">
              <span className="filter-label">Saralash</span>
              <select
                className="filter-control"
                value={sortField}
                onChange={(e) => setSortField(e.target.value as Exclude<SortField, "done_at">)}
              >
                {Object.entries(SORT_FIELD_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
              <button
                className="btn btn--ghost sort-dir-btn"
                onClick={() => setSortDir((d) => (d === "desc" ? "asc" : "desc"))}
              >
                <ArrowDownUp size={15} />
                {sortDir === "desc" ? "Yangi birinchi" : "Eski birinchi"}
              </button>
            </div>
          )}
          {view === "archive" && (
            <>
              <input
                className="filter-search"
                placeholder="Vazifa yoki loyiha qidirish…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <div className="filter-item">
                <span className="filter-label">Saralash</span>
                <button
                  className="btn btn--ghost sort-dir-btn"
                  onClick={() => setArchiveDir((d) => (d === "desc" ? "asc" : "desc"))}
                >
                  <ArrowDownUp size={15} />
                  {archiveDir === "desc" ? "Eng yangi" : "Eng eski"}
                </button>
              </div>
            </>
          )}
          {hasFilter && (
            <button className="btn btn--ghost filter-clear" onClick={clearFilters}>
              <X size={15} /> Tozalash
            </button>
          )}
        </div>
      )}

      {/* ── Filtr paneli (mobil Ro'yxat): qidiruv + davr + tezkor chip'lar ── */}
      {view === "list" && isMobile && (
        <div className="mobile-filter-bar">
          <div className="mobile-filter-bar__row">
            <input
              className="filter-search"
              placeholder="Vazifa yoki loyiha qidirish…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <DateFilter value={range} onChange={setRange} compactLabel="Muddat" />
          </div>
          <div className="quick-chips">
            {QUICK_FILTERS.map((q) => (
              <button
                key={q.key}
                className={`quick-chip${quickFilter === q.key ? " active" : ""}`}
                onClick={() => setQuickFilter(q.key)}
              >
                {q.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Ko'rinish ── */}
      {view === "board" && (
        <DndContext sensors={sensors} onDragEnd={onDragEnd}>
          <div className="board">
            {columns.map((col) => {
              const colTasks = boardTasks.filter((tk) => tk.status === col.key);
              return (
                <Column key={col.key} column={col} count={colTasks.length}>
                  {colTasks.map((tk) => (
                    <TaskCard
                      key={tk.id}
                      task={tk}
                      dep={deps.find((d) => d.id === tk.dep_id)}
                      onClick={openTask}
                    />
                  ))}
                </Column>
              );
            })}
          </div>
        </DndContext>
      )}

      {view === "list" && (
        <div className="tasks-panel">
          {isMobile ? (
            <MobileTaskList
              tasks={listTasks}
              columns={columns}
              deps={deps}
              doneKeys={doneKeys}
              canEdit={canEditTask}
              canDelete={canEditTask}
              canMarkDone={isBoss}
              onOpen={openTask}
              onEdit={openTask}
              onDelete={deleteTask}
              onMarkDone={openConfirmDone}
              onArchive={() => setView("archive")}
            />
          ) : (
            <TasksTable tasks={listTasks} columns={columns} deps={deps} variant="list" onOpen={openTask} />
          )}
        </div>
      )}

      {view === "archive" && (
        <div className="tasks-panel">
          <div className="archive-stats">
            <div className="stat-card"><div className="stat-card__label">Jami arxiv</div><div className="stat-card__num">{doneAll.length}</div></div>
            <div className="stat-card"><div className="stat-card__label">Bu yil</div><div className="stat-card__num" style={{ color: "var(--accent)" }}>{doneYear.length}</div></div>
            <div className="stat-card"><div className="stat-card__label">Bu oy</div><div className="stat-card__num" style={{ color: "var(--ok)" }}>{doneMonth.length}</div></div>
          </div>
          <TasksTable
            tasks={archiveTasks}
            columns={columns}
            deps={deps}
            variant="archive"
            onOpen={openTask}
            onRestore={isObserver ? undefined : restore}
            restoringId={restoringId}
          />
        </div>
      )}

      {formOpen && (
        <TaskForm
          key={editing?.id ?? "new"}
          task={editing}
          isBoss={isBoss}
          isObserver={isObserver}
          autoConfirmDone={autoConfirm}
          onClose={() => setFormOpen(false)}
          onSaved={() => { setFormOpen(false); load(); }}
          onStatusChanged={(updated) => {
            setTasks((prev) => prev.map((tk) => (tk.id === updated.id ? updated : tk)));
            setEditing(updated);
          }}
        />
      )}
    </div>
  );
}

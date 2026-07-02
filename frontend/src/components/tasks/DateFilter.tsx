import { useEffect, useMemo, useRef, useState } from "react";
import { Calendar, ChevronLeft, ChevronRight } from "lucide-react";

export type RangeMode = "all" | "day" | "week" | "month" | "year";

export interface DateRange {
  mode: RangeMode;
  /** YYYY-MM-DD (inklyuziv boshlanish) yoki null = cheklovsiz */
  from: string | null;
  /** YYYY-MM-DD (inklyuziv tugash) yoki null = cheklovsiz */
  to: string | null;
}

export const ALL_TIME: DateRange = { mode: "all", from: null, to: null };

const WEEKDAYS = ["Du", "Se", "Cho", "Pa", "Ju", "Sha", "Ya"];
const MONTHS = [
  "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
];

// ── sana yordamchilari (mahalliy vaqt) ──────────────────
function iso(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}
function parse(s: string): Date {
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y, m - 1, d);
}
/** Dushanba = hafta boshi */
function startOfWeek(d: Date): Date {
  const x = new Date(d);
  const wd = (x.getDay() + 6) % 7; // Du=0 … Ya=6
  x.setDate(x.getDate() - wd);
  return x;
}
function sameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}
function inRange(d: Date, from: string | null, to: string | null): boolean {
  const s = iso(d);
  if (from && s < from) return false;
  if (to && s > to) return false;
  return true;
}

export function formatRange(r: DateRange): string {
  if (r.mode === "all" || !r.from) return "Barcha vaqt";
  const f = parse(r.from);
  if (r.mode === "day") return `${f.getDate()} ${MONTHS[f.getMonth()]} ${f.getFullYear()}`;
  if (r.mode === "year") return String(f.getFullYear());
  if (r.mode === "month") return `${MONTHS[f.getMonth()]} ${f.getFullYear()}`;
  // week
  const t = r.to ? parse(r.to) : f;
  return `${f.getDate()} – ${t.getDate()} ${MONTHS[t.getMonth()]} ${t.getFullYear()}`;
}

interface Props {
  value: DateRange;
  onChange: (r: DateRange) => void;
  /** Berilsa, tugma matni doim shu (masalan "Muddat") — ixcham mobil ko'rinish uchun */
  compactLabel?: string;
}

export function DateFilter({ value, onChange, compactLabel }: Props) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<RangeMode>(value.mode === "all" ? "day" : value.mode);
  const [cursor, setCursor] = useState<Date>(value.from ? parse(value.from) : new Date());
  const [yearBase, setYearBase] = useState<number>(() => {
    const y = value.from ? parse(value.from).getFullYear() : new Date().getFullYear();
    return y - (y % 12) - 1;
  });
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  function pick(range: DateRange) {
    onChange(range);
    setOpen(false);
  }

  function pickDay(d: Date) {
    if (mode === "day") pick({ mode: "day", from: iso(d), to: iso(d) });
    else if (mode === "week") {
      const s = startOfWeek(d);
      const e = new Date(s);
      e.setDate(s.getDate() + 6);
      pick({ mode: "week", from: iso(s), to: iso(e) });
    } else if (mode === "month") {
      const s = new Date(d.getFullYear(), d.getMonth(), 1);
      const e = new Date(d.getFullYear(), d.getMonth() + 1, 0);
      pick({ mode: "month", from: iso(s), to: iso(e) });
    }
  }

  function pickMonth(m: number) {
    const s = new Date(cursor.getFullYear(), m, 1);
    const e = new Date(cursor.getFullYear(), m + 1, 0);
    pick({ mode: "month", from: iso(s), to: iso(e) });
  }

  function pickYear(y: number) {
    pick({ mode: "year", from: iso(new Date(y, 0, 1)), to: iso(new Date(y, 11, 31)) });
  }

  // Oy panjarasi (Kun/Hafta/Oy rejimlarida)
  const grid = useMemo(() => {
    const first = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
    const start = startOfWeek(first);
    return Array.from({ length: 42 }, (_, i) => {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      return d;
    });
  }, [cursor]);

  const today = new Date();
  const showCalendar = mode === "day" || mode === "week" || mode === "month";

  return (
    <div className="date-filter" ref={rootRef}>
      <button className="filter-control" onClick={() => setOpen((v) => !v)}>
        <Calendar size={16} />
        <span>{compactLabel || formatRange(value)}</span>
        <ChevronRight size={15} className={`date-filter__caret${open ? " open" : ""}`} />
      </button>

      {open && (
        <div className="date-pop">
          <div className="date-pop__modes">
            {(["day", "week", "month", "year"] as RangeMode[]).map((m) => (
              <button
                key={m}
                className={`seg${mode === m ? " active" : ""}`}
                onClick={() => setMode(m)}
              >
                {m === "day" ? "Kun" : m === "week" ? "Hafta" : m === "month" ? "Oy" : "Yil"}
              </button>
            ))}
          </div>

          {showCalendar && (
            <>
              <div className="date-pop__nav">
                <button onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() - 1, 1))}>
                  <ChevronLeft size={18} />
                </button>
                <span>{MONTHS[cursor.getMonth()]} {cursor.getFullYear()}</span>
                <button onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1))}>
                  <ChevronRight size={18} />
                </button>
              </div>

              {mode === "month" ? (
                <div className="date-pop__months">
                  {MONTHS.map((mn, i) => (
                    <button
                      key={mn}
                      className={`date-cell wide${value.from && parse(value.from).getMonth() === i && parse(value.from).getFullYear() === cursor.getFullYear() ? " sel" : ""}`}
                      onClick={() => pickMonth(i)}
                    >
                      {mn.slice(0, 3)}
                    </button>
                  ))}
                </div>
              ) : (
                <>
                  <div className="date-pop__week">
                    {WEEKDAYS.map((w) => (
                      <span key={w}>{w}</span>
                    ))}
                  </div>
                  <div className="date-pop__grid">
                    {grid.map((d, i) => {
                      const muted = d.getMonth() !== cursor.getMonth();
                      const sel = inRange(d, value.from, value.to) && value.mode !== "all";
                      const isToday = sameDay(d, today);
                      return (
                        <button
                          key={i}
                          className={`date-cell${muted ? " muted" : ""}${sel ? " sel" : ""}${isToday ? " today" : ""}`}
                          onClick={() => pickDay(d)}
                        >
                          {d.getDate()}
                        </button>
                      );
                    })}
                  </div>
                </>
              )}
            </>
          )}

          {mode === "year" && (
            <>
              <div className="date-pop__nav">
                <button onClick={() => setYearBase(yearBase - 12)}>
                  <ChevronLeft size={18} />
                </button>
                <span>{yearBase + 1} – {yearBase + 12}</span>
                <button onClick={() => setYearBase(yearBase + 12)}>
                  <ChevronRight size={18} />
                </button>
              </div>
              <div className="date-pop__months">
                {Array.from({ length: 12 }, (_, i) => yearBase + 1 + i).map((y) => (
                  <button
                    key={y}
                    className={`date-cell wide${value.from && parse(value.from).getFullYear() === y ? " sel" : ""}`}
                    onClick={() => pickYear(y)}
                  >
                    {y}
                  </button>
                ))}
              </div>
            </>
          )}

          <div className="date-pop__foot">
            <button className="btn btn--ghost" onClick={() => pick(ALL_TIME)}>
              Barcha vaqt
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

import type { Lang } from "../i18n";

const LABELS: Record<Lang, { today: string; left: (n: number) => string; over: (n: number) => string }> = {
  uz: {
    today: "Bugun",
    left: (n) => `${n} kun qoldi`,
    over: (n) => `${n} kun kechikdi`,
  },
  ru: {
    today: "Сегодня",
    left: (n) => `Осталось ${n} дн.`,
    over: (n) => `Просрочено на ${n} дн.`,
  },
  en: {
    today: "Today",
    left: (n) => `${n} day(s) left`,
    over: (n) => `${n} day(s) overdue`,
  },
};

/** Sana + (agar bo'lsa) vaqtni ko'rsatish: "15.06.2026" yoki "15.06.2026 14:00" */
export function formatDeadlineDate(value: string): string {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  const hasTime = d.getHours() !== 0 || d.getMinutes() !== 0;
  const opts: Intl.DateTimeFormatOptions = hasTime
    ? { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }
    : { day: "2-digit", month: "2-digit", year: "numeric" };
  return d.toLocaleString(undefined, opts);
}

/** "3 kun qoldi" / "Bugun" / "5 kun kechikdi" */
export function formatCountdown(value: string, lang: Lang): string {
  const target = new Date(value);
  if (Number.isNaN(target.getTime())) return "";
  const now = new Date();
  const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const diffDays = Math.round(
    (startOfDay(target).getTime() - startOfDay(now).getTime()) / 86400000
  );
  const l = LABELS[lang] ?? LABELS.uz;
  if (diffDays === 0) return l.today;
  if (diffDays > 0) return l.left(diffDays);
  return l.over(Math.abs(diffDays));
}

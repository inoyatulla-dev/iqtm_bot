import type { Lang } from "../i18n";
import { formatDeadlineDate } from "./deadline";

// Backend "created_at"/"updated_at" qiymatlari vaqt zonasiz (naive) saqlanadi —
// ular server OS vaqt zonasidagi (Asia/Tashkent) devor vaqtini bildiradi.
const SERVER_TZ = "Asia/Tashkent";

function getTimezoneOffsetMs(date: Date, timeZone: string): number {
  const tzDate = new Date(date.toLocaleString("en-US", { timeZone }));
  const utcDate = new Date(date.toLocaleString("en-US", { timeZone: "UTC" }));
  return tzDate.getTime() - utcDate.getTime();
}

/** Naive server vaqtini (Asia/Tashkent devor vaqti) haqiqiy UTC lahzasiga aylantiradi. */
function parseServerDate(value: string): Date | null {
  const naive = new Date(value.endsWith("Z") ? value : `${value}Z`);
  if (Number.isNaN(naive.getTime())) return null;
  const offsetMs = getTimezoneOffsetMs(naive, SERVER_TZ);
  return new Date(naive.getTime() - offsetMs);
}

/** Server timestamp'ini tanlangan vaqt zonasida "kun.oy, soat:daqiqa" ko'rinishida formatlaydi. */
export function formatDateTime(value: string | undefined | null, timeZone: string): string {
  if (!value) return "";
  const d = parseServerDate(value);
  if (!d) return value;
  return new Intl.DateTimeFormat(undefined, {
    day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
    timeZone,
  }).format(d);
}

const AGO_LABELS: Record<Lang, {
  now: string; min: (n: number) => string; hour: (n: number) => string;
  yesterday: string; day: (n: number) => string;
}> = {
  uz: {
    now: "hozirgina",
    min: (n) => `${n} daqiqa oldin`,
    hour: (n) => `${n} soat oldin`,
    yesterday: "Kecha",
    day: (n) => `${n} kun oldin`,
  },
  ru: {
    now: "только что",
    min: (n) => `${n} мин. назад`,
    hour: (n) => `${n} ч. назад`,
    yesterday: "Вчера",
    day: (n) => `${n} дн. назад`,
  },
  en: {
    now: "just now",
    min: (n) => `${n}m ago`,
    hour: (n) => `${n}h ago`,
    yesterday: "Yesterday",
    day: (n) => `${n}d ago`,
  },
};

/** Nisbiy vaqt: "5 daqiqa oldin" / "2 soat oldin" / "Kecha" / to'liq sana (eskiroq). */
export function formatTimeAgo(value: string, lang: Lang): string {
  const d = parseServerDate(value);
  if (!d) return value;
  const l = AGO_LABELS[lang] ?? AGO_LABELS.uz;
  const diffMin = Math.floor((Date.now() - d.getTime()) / 60000);
  if (diffMin < 1) return l.now;
  if (diffMin < 60) return l.min(diffMin);
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return l.hour(diffHour);
  const diffDay = Math.floor(diffHour / 24);
  if (diffDay === 1) return l.yesterday;
  if (diffDay < 7) return l.day(diffDay);
  return formatDeadlineDate(value);
}

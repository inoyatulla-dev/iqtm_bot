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

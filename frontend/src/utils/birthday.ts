const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());

/** Tug'ilgan kungacha necha kun qolganini hisoblaydi (0 = bugun). */
export function birthdayInDays(birthday?: string | null): number | null {
  if (!birthday) return null;
  const parts = birthday.split("-").map(Number);
  const month = parts[1];
  const day = parts[2];
  if (!month || !day) return null;
  const today = new Date();
  let next = new Date(today.getFullYear(), month - 1, day);
  if (next < startOfDay(today)) next = new Date(today.getFullYear() + 1, month - 1, day);
  return Math.round((startOfDay(next).getTime() - startOfDay(today).getTime()) / 86400000);
}

/** "12-iyul" kabi sana ko'rinishi (kun.oy raqamli, masalan "12.07"). */
export function formatBirthdayDate(birthday: string): string {
  const parts = birthday.split("-").map(Number);
  const month = parts[1];
  const day = parts[2];
  if (!month || !day) return birthday;
  return `${String(day).padStart(2, "0")}.${String(month).padStart(2, "0")}`;
}

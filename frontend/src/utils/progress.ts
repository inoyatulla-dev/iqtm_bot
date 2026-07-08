/** Progress-bar to'ldirilishi uchun rang: 100% — yashil, 0% dan katta — ko'k, 0% — sariq. */
export function progressColor(percent: number): string {
  if (percent >= 100) return "var(--ok)";
  if (percent > 0) return "var(--accent)";
  return "var(--warn)";
}

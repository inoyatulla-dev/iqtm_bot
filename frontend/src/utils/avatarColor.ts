const PALETTE: [string, string][] = [
  ["#3b82f6", "#6366f1"],
  ["#22c55e", "#16a34a"],
  ["#f59e0b", "#ea580c"],
  ["#a855f7", "#7c3aed"],
  ["#ef4444", "#b91c1c"],
  ["#06b6d4", "#0891b2"],
];

export function avatarGradient(id: number): string {
  const [a, b] = PALETTE[id % PALETTE.length];
  return `linear-gradient(135deg, ${a}, ${b})`;
}

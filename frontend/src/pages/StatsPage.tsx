import { useEffect, useState } from "react";
import { statsApi } from "../api/client";
import type { RatingRow, StatusCounts } from "../api/types";
import { useAuth } from "../store/auth";

export function StatsPage() {
  const { isBoss } = useAuth();
  const [counts, setCounts] = useState<StatusCounts | null>(null);
  const [rating, setRating] = useState<RatingRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const c = isBoss ? await statsApi.global() : await statsApi.me();
      setCounts(c);
      if (isBoss) setRating(await statsApi.rating());
      setLoading(false);
    })();
  }, [isBoss]);

  if (loading || !counts) return <div className="center-screen">Yuklanmoqda…</div>;

  const cards = [
    { num: counts.total, label: "Jami", color: "var(--text)" },
    { num: counts.new, label: "🆕 Yangi", color: "#64748b" },
    { num: counts.in_progress, label: "🔄 Jarayonda", color: "#f59e0b" },
    { num: counts.review, label: "🔍 Tekshiruvda", color: "#8b5cf6" },
    { num: counts.done, label: "✅ Bajarildi", color: "#10b981" },
    { num: counts.overdue, label: "⚠️ Kechikkan", color: "#ff5a5a" },
  ];
  const medal = (i: number) => ["🥇", "🥈", "🥉"][i] || `${i + 1}.`;

  return (
    <div style={{ paddingBottom: 90 }}>
      <div className="section-title">
        {isBoss ? "📊 Umumiy statistika" : "📊 Mening statistikam"}
      </div>
      <div className="stat-grid">
        {cards.map((c) => (
          <div className="stat-card" key={c.label}>
            <div className="stat-card__num" style={{ color: c.color }}>
              {c.num}
            </div>
            <div className="stat-card__label">{c.label}</div>
          </div>
        ))}
      </div>

      {isBoss && rating.length > 0 && (
        <>
          <div className="section-title">🏆 Xodimlar reytingi</div>
          {rating.map((r, i) => (
            <div className="list-item" key={r.user_id}>
              <span style={{ fontSize: 20, width: 28, textAlign: "center" }}>{medal(i)}</span>
              <div className="list-item__body">
                <div className="list-item__title">{r.name}</div>
                <div className="list-item__sub">
                  ✅ {r.done} · 🔄 {r.active} · ⚠️ {r.overdue}
                </div>
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

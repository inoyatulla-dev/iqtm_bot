import { useEffect, useState } from "react";
import { statsApi } from "../api/client";
import type { RatingRow, StatusCounts } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";

export function StatsPage() {
  const { isBoss } = useAuth();
  const { t } = useI18n();
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

  if (loading || !counts) return <div className="center-screen">{t("common.loading")}</div>;

  const cards = [
    { num: counts.total, label: t("stats.total"), color: "var(--text)" },
    { num: counts.new, label: `🆕 ${t("status.new")}`, color: "#64748b" },
    { num: counts.in_progress, label: `🔄 ${t("status.in_progress")}`, color: "#f59e0b" },
    { num: counts.review, label: `🔍 ${t("status.review")}`, color: "#8b5cf6" },
    { num: counts.done, label: `✅ ${t("status.done")}`, color: "#10b981" },
    { num: counts.overdue, label: `⚠️ ${t("stats.overdue")}`, color: "#ff5a5a" },
  ];
  const medal = (i: number) => ["🥇", "🥈", "🥉"][i] || `${i + 1}.`;

  return (
    <div style={{ paddingBottom: 90 }}>
      <div className="section-title">
        {isBoss ? t("stats.titleGlobal") : t("stats.titleMy")}
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
          <div className="section-title">{t("stats.rating")}</div>
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

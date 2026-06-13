import { useEffect, useState } from "react";
import { statsApi } from "../api/client";
import type { ReportPeriod } from "../api/client";
import type { RatingRow, StatusCounts } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";

const PERIODS: ReportPeriod[] = ["week", "month", "year"];

export function StatsPage() {
  const { isBoss, columns } = useAuth();
  const { t } = useI18n();
  const [counts, setCounts] = useState<StatusCounts | null>(null);
  const [rating, setRating] = useState<RatingRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<ReportPeriod>("week");

  useEffect(() => {
    (async () => {
      setLoading(true);
      const c = isBoss ? await statsApi.global(period) : await statsApi.me(period);
      setCounts(c);
      if (isBoss) setRating(await statsApi.rating(period));
      setLoading(false);
    })();
  }, [isBoss, period]);

  if (loading || !counts) return <div className="center-screen">{t("common.loading")}</div>;

  const cards = [
    { num: counts.total, label: t("stats.total"), color: "var(--text)" },
    ...columns.map((col) => ({
      num: counts.counts[col.key] || 0,
      label: `${col.emoji} ${col.name}`,
      color: col.color,
    })),
    { num: counts.overdue, label: `⚠️ ${t("stats.overdue")}`, color: "#ff5a5a" },
    { num: counts.done_in_period, label: `✅ ${t("stats.doneInPeriod")}`, color: "var(--ok)" },
  ];
  const medal = (i: number) => ["🥇", "🥈", "🥉"][i] || `${i + 1}.`;
  const maxDone = Math.max(1, ...rating.map((r) => r.done_in_period));

  return (
    <div className="page-content">
      <div className="section-title">
        {isBoss ? t("stats.titleGlobal") : t("stats.titleMy")}
      </div>

      <div className="report-row" style={{ marginBottom: 16 }}>
        {PERIODS.map((p) => (
          <button
            key={p}
            className={`btn ${period === p ? "btn--primary" : "btn--ghost"}`}
            onClick={() => setPeriod(p)}
          >
            {t(`stats.period.${p}`)}
          </button>
        ))}
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

          <div className="section-title">{t("stats.efficiency")}</div>
          <div className="card">
            {rating.map((r) => (
              <div className="dept-row" key={r.user_id}>
                <div className="dept-row__head">
                  <div className="dept-row__name">{r.name}</div>
                  <div className="dept-row__count">{r.done_in_period}</div>
                </div>
                <div className="progress-bar">
                  <div
                    className="progress-bar__fill"
                    style={{ width: `${(r.done_in_period / maxDone) * 100}%`, background: "var(--accent)" }}
                  />
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

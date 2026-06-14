import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Medal, RefreshCw } from "lucide-react";
import { EmojiIcon } from "../utils/emojiIcon";
import { statsApi } from "../api/client";
import type { RatingRow, StatusCounts } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";
import { PeriodPicker, defaultPeriodValue, toPeriodParams, type PeriodValue } from "../components/PeriodPicker";

export function StatsPage() {
  const { isBoss, columns } = useAuth();
  const { t } = useI18n();
  const [counts, setCounts] = useState<StatusCounts | null>(null);
  const [rating, setRating] = useState<RatingRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<PeriodValue>(() => defaultPeriodValue("week"));

  useEffect(() => {
    (async () => {
      setLoading(true);
      const params = toPeriodParams(period);
      const c = isBoss ? await statsApi.global(period.period, params) : await statsApi.me(period.period, params);
      setCounts(c);
      if (isBoss) setRating(await statsApi.rating(period.period, params));
      setLoading(false);
    })();
  }, [isBoss, period]);

  if (loading || !counts) return <div className="center-screen">{t("common.loading")}</div>;

  const cards = [
    { num: counts.total, label: t("stats.total"), color: "var(--text)" },
    ...columns.map((col) => ({
      num: counts.counts[col.key] || 0,
      label: col.name,
      color: col.color,
      icon: <EmojiIcon emoji={col.emoji} color={col.color} size={14} />,
    })),
    { num: counts.overdue, label: t("stats.overdue"), color: "#ff5a5a", icon: <AlertTriangle size={14} /> },
    { num: counts.done_in_period, label: t("stats.doneInPeriod"), color: "var(--ok)", icon: <CheckCircle2 size={14} /> },
  ];
  const medalColors = ["#FFD700", "#C0C0C0", "#CD7F32"];
  const medal = (i: number) =>
    i < 3 ? <Medal size={20} color={medalColors[i]} /> : <span>{i + 1}.</span>;
  const maxDone = Math.max(1, ...rating.map((r) => r.done_in_period));

  return (
    <div className="page-content">
      <div className="section-title">
        {isBoss ? t("stats.titleGlobal") : t("stats.titleMy")}
      </div>

      <PeriodPicker value={period} onChange={setPeriod} />

      <div className="stat-grid">
        {cards.map((c) => (
          <div className="stat-card" key={c.label}>
            <div className="stat-card__num" style={{ color: c.color }}>
              {c.num}
            </div>
            <div className="stat-card__label" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 4 }}>
              {"icon" in c && c.icon}{c.label}
            </div>
          </div>
        ))}
      </div>

      {isBoss && rating.length > 0 && (
        <>
          <div className="section-title">{t("stats.rating")}</div>
          {rating.map((r, i) => (
            <div className="list-item" key={r.user_id}>
              <span style={{ width: 28, display: "inline-flex", justifyContent: "center" }}>{medal(i)}</span>
              <div className="list-item__body">
                <div className="list-item__title">{r.name}</div>
                <div className="list-item__sub" style={{ display: "flex", alignItems: "center", gap: 4, flexWrap: "wrap" }}>
                  <CheckCircle2 size={14} /> {r.done} · <RefreshCw size={14} /> {r.active} · <AlertTriangle size={14} /> {r.overdue}
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

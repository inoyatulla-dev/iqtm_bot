import { useEffect, useState } from "react";
import { reportsApi, statsApi } from "../api/client";
import type { ReportFormat, ReportPeriod } from "../api/client";
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
  const [reportBusy, setReportBusy] = useState(false);

  useEffect(() => {
    (async () => {
      const c = isBoss ? await statsApi.global() : await statsApi.me();
      setCounts(c);
      if (isBoss) setRating(await statsApi.rating());
      setLoading(false);
    })();
  }, [isBoss]);

  async function downloadReport(fmt: ReportFormat) {
    setReportBusy(true);
    try {
      const blob = await reportsApi.download(period, fmt);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `hisobot_${period}.${fmt}`;
      link.click();
      URL.revokeObjectURL(url);
    } finally {
      setReportBusy(false);
    }
  }

  if (loading || !counts) return <div className="center-screen">{t("common.loading")}</div>;

  const cards = [
    { num: counts.total, label: t("stats.total"), color: "var(--text)" },
    ...columns.map((col) => ({
      num: counts.counts[col.key] || 0,
      label: `${col.emoji} ${col.name}`,
      color: col.color,
    })),
    { num: counts.overdue, label: `⚠️ ${t("stats.overdue")}`, color: "#ff5a5a" },
  ];
  const medal = (i: number) => ["🥇", "🥈", "🥉"][i] || `${i + 1}.`;

  return (
    <div className="page-content">
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

      {isBoss && (
        <>
          <div className="section-title">{t("stats.reports")}</div>
          <div className="report-controls">
            <div className="report-row">
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
            <div className="report-row">
              <button className="btn btn--ghost" onClick={() => downloadReport("pdf")} disabled={reportBusy}>
                📄 {t("stats.downloadPdf")}
              </button>
              <button className="btn btn--ghost" onClick={() => downloadReport("docx")} disabled={reportBusy}>
                📝 {t("stats.downloadDocx")}
              </button>
              <button className="btn btn--ghost" onClick={() => downloadReport("xlsx")} disabled={reportBusy}>
                📊 {t("stats.downloadExcel")}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

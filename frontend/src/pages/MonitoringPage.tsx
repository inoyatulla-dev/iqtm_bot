import { useEffect, useState } from "react";
import { FileText, FileType } from "lucide-react";
import { reportsApi, statsApi } from "../api/client";
import type { ReportFormat } from "../api/client";
import type { DashboardData } from "../api/types";
import { useI18n } from "../i18n";
import { PeriodPicker, defaultPeriodValue, toPeriodParams, type PeriodValue } from "../components/PeriodPicker";
import { EmojiIcon } from "../utils/emojiIcon";

export function MonitoringPage() {
  const { t } = useI18n();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<PeriodValue>(() => defaultPeriodValue("month"));
  const [downloading, setDownloading] = useState<ReportFormat | null>(null);

  useEffect(() => {
    setLoading(true);
    statsApi.dashboard(period.period, toPeriodParams(period)).then((d) => {
      setData(d);
      setLoading(false);
    });
  }, [period]);

  async function downloadReport(fmt: ReportFormat) {
    setDownloading(fmt);
    try {
      const blob = await reportsApi.download(period.period, fmt, toPeriodParams(period));
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `hisobot_${period.period}.${fmt}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(e?.response?.data?.detail || t("common.error"));
    } finally {
      setDownloading(null);
    }
  }

  if (loading || !data) return <div className="center-screen">{t("common.loading")}</div>;

  let acc = 0;
  const conic = data.distribution
    .map((seg, i) => {
      const start = acc;
      acc += seg.percent;
      const end = i === data.distribution.length - 1 ? 100 : acc;
      return `${seg.color} ${start}% ${end}%`;
    })
    .join(", ");

  return (
    <div className="page-content">
      <PeriodPicker value={period} onChange={setPeriod} />

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-card__num">{data.total}</div>
          <div className="stat-card__label">{t("monitoring.total")}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__num" style={{ color: "var(--ok)" }}>{data.done}</div>
          <div className="stat-card__label">{t("monitoring.done")}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__num" style={{ color: "var(--accent)" }}>{data.in_progress}</div>
          <div className="stat-card__label">{t("monitoring.inProgress")}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__num" style={{ color: "var(--danger)" }}>{data.overdue}</div>
          <div className="stat-card__label">{t("monitoring.overdue")}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__num">{data.new_in_period}</div>
          <div className="stat-card__label">{t("monitoring.newInPeriod")}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__num">{data.closed_in_period}</div>
          <div className="stat-card__label">{t("monitoring.closedInPeriod")}</div>
        </div>
      </div>

      <div className="section-title">{t("monitoring.byDept")}</div>
      <div className="card">
        {data.departments.length === 0 ? (
          <div className="empty-state">{t("monitoring.noTasks")}</div>
        ) : (
          data.departments.map((d) => (
            <div className="dept-row" key={d.dep_id}>
              <div className="dept-row__head">
                <div className="dept-row__name">
                  <span className="dot" style={{ background: d.color }} />
                  <EmojiIcon emoji={d.emoji} size={14} color={d.color} /> {d.name}
                </div>
                <div className="dept-row__count">
                  {d.done} / {d.total} · {d.percent}%
                </div>
              </div>
              <div className="progress-bar">
                <div className="progress-bar__fill" style={{ width: `${d.percent}%`, background: d.color }} />
              </div>
            </div>
          ))
        )}
      </div>

      <div className="section-title">{t("monitoring.distribution")}</div>
      <div className="card donut-wrap">
        <div className="donut" style={{ background: data.total ? `conic-gradient(${conic})` : "var(--surface)" }} />
        <div className="donut-legend">
          {data.distribution.map((seg) => (
            <span key={seg.key}>
              <span className="legend-dot" style={{ background: seg.color }} />
              {t(`monitoring.dist.${seg.key}`)} — {seg.percent}%
            </span>
          ))}
        </div>
      </div>

      <div className="section-title">{t("monitoring.exportTitle")}</div>
      <div className="report-controls">
        <div className="report-row">
          <button className="btn btn--ghost" onClick={() => downloadReport("pdf")} disabled={!!downloading}>
            {downloading === "pdf" ? t("monitoring.downloading") : <><FileText size={18} /> {t("stats.downloadPdf")}</>}
          </button>
          <button className="btn btn--ghost" onClick={() => downloadReport("docx")} disabled={!!downloading}>
            {downloading === "docx" ? t("monitoring.downloading") : <><FileType size={18} /> {t("stats.downloadDocx")}</>}
          </button>
        </div>
      </div>
    </div>
  );
}

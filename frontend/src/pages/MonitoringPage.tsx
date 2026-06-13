import { useEffect, useState } from "react";
import { statsApi } from "../api/client";
import type { DashboardData } from "../api/types";
import { useI18n } from "../i18n";

export function MonitoringPage() {
  const { t } = useI18n();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    statsApi.dashboard().then((d) => {
      setData(d);
      setLoading(false);
    });
  }, []);

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
          <div className="stat-card__num">{data.new_this_month}</div>
          <div className="stat-card__label">{t("monitoring.newThisMonth")}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__num">{data.closed_this_month}</div>
          <div className="stat-card__label">{t("monitoring.closedThisMonth")}</div>
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
                  {d.emoji} {d.name}
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
    </div>
  );
}

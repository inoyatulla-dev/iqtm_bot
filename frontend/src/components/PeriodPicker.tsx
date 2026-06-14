import { useState } from "react";
import { Calendar } from "lucide-react";
import type { PeriodParams, ReportPeriod } from "../api/client";
import { useI18n } from "../i18n";

export interface PeriodValue {
  period: ReportPeriod;
  year?: number;
  month?: number;
  date_from?: string;
  date_to?: string;
}

const PERIODS: ReportPeriod[] = ["week", "month", "year"];
const MONTHS = Array.from({ length: 12 }, (_, i) => i + 1);

export function defaultPeriodValue(period: ReportPeriod = "month"): PeriodValue {
  const now = new Date();
  return { period, year: now.getFullYear(), month: now.getMonth() + 1 };
}

export function toPeriodParams(value: PeriodValue): PeriodParams {
  if (value.date_from && value.date_to) {
    return { date_from: value.date_from, date_to: value.date_to };
  }
  if (value.period === "year" && value.year) {
    return { year: value.year };
  }
  if (value.period === "month" && value.year && value.month) {
    return { year: value.year, month: value.month };
  }
  return {};
}

interface PeriodPickerProps {
  value: PeriodValue;
  onChange: (value: PeriodValue) => void;
}

export function PeriodPicker({ value, onChange }: PeriodPickerProps) {
  const { t } = useI18n();
  const [customOpen, setCustomOpen] = useState(false);
  const [from, setFrom] = useState(value.date_from || "");
  const [to, setTo] = useState(value.date_to || "");

  const now = new Date();
  const years = Array.from({ length: 6 }, (_, i) => now.getFullYear() - i);
  const isCustom = !!(value.date_from && value.date_to);

  function selectPeriod(period: ReportPeriod) {
    setCustomOpen(false);
    if (period === "month") {
      onChange({ period, year: value.year || now.getFullYear(), month: value.month || now.getMonth() + 1 });
    } else if (period === "year") {
      onChange({ period, year: value.year || now.getFullYear() });
    } else {
      onChange({ period });
    }
  }

  function toggleCustom() {
    if (isCustom) {
      onChange({ ...value, date_from: undefined, date_to: undefined });
      setCustomOpen(false);
    } else {
      setCustomOpen((v) => !v);
    }
  }

  function applyCustom() {
    if (!from || !to) return;
    onChange({ ...value, date_from: from, date_to: to });
    setCustomOpen(false);
  }

  function clearCustom() {
    setFrom("");
    setTo("");
    onChange({ ...value, date_from: undefined, date_to: undefined });
    setCustomOpen(false);
  }

  return (
    <>
      <div className="report-row period-row">
        {PERIODS.map((p) => (
          <button
            key={p}
            className={`btn ${!isCustom && value.period === p ? "btn--primary" : "btn--ghost"}`}
            onClick={() => selectPeriod(p)}
          >
            {t(`stats.period.${p}`)}
          </button>
        ))}
        <button className={`btn ${isCustom || customOpen ? "btn--primary" : "btn--ghost"}`} onClick={toggleCustom}>
          {t("stats.customRange")}
        </button>
      </div>

      {!isCustom && !customOpen && value.period === "month" && (
        <div className="report-row period-extra">
          <select value={value.month} onChange={(e) => onChange({ ...value, month: Number(e.target.value) })}>
            {MONTHS.map((m) => (
              <option key={m} value={m}>{t(`stats.month.${m}`)}</option>
            ))}
          </select>
          <select value={value.year} onChange={(e) => onChange({ ...value, year: Number(e.target.value) })}>
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      )}

      {!isCustom && !customOpen && value.period === "year" && (
        <div className="report-row period-extra">
          <select value={value.year} onChange={(e) => onChange({ ...value, year: Number(e.target.value) })}>
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      )}

      {customOpen && (
        <div className="report-row period-extra">
          <div className="date-field">
            <span className="date-field__label">{t("stats.dateFrom")}</span>
            <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} max={to || undefined} />
          </div>
          <div className="date-field">
            <span className="date-field__label">{t("stats.dateTo")}</span>
            <input type="date" value={to} onChange={(e) => setTo(e.target.value)} min={from || undefined} />
          </div>
          <button className="btn btn--primary" onClick={applyCustom} disabled={!from || !to}>
            {t("stats.apply")}
          </button>
        </div>
      )}

      {isCustom && (
        <div className="report-row period-extra">
          <span className="period-extra__hint">
            <Calendar size={15} />
            {value.date_from} — {value.date_to}
          </span>
          <button className="btn btn--ghost" onClick={clearCustom}>{t("stats.clear")}</button>
        </div>
      )}
    </>
  );
}

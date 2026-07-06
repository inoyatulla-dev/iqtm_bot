import { useState } from "react";

interface Props {
  /** "HH:MM" yoki bo'sh */
  value: string;
  onCancel: () => void;
  onConfirm: (value: string) => void;
}

const R = 88; // radiusi (clock-face 220px, markaz 110)
const CENTER = 110;

/** Analog soat picker — avval soat, keyin daqiqa tanlanadi (12 soatlik + AM/PM). */
export function ClockPicker({ value, onCancel, onConfirm }: Props) {
  const init = /^\d{1,2}:\d{2}$/.test(value) ? value : "09:00";
  const [h, m] = init.split(":").map(Number);
  const [hour, setHour] = useState(h); // 24 soatlik format (0-23) — saqlanadigan qiymat
  const [minute, setMinute] = useState(m);
  const [stage, setStage] = useState<"hour" | "minute">("hour");

  const period: "AM" | "PM" = hour >= 12 ? "PM" : "AM";
  const displayHour = hour % 12 === 0 ? 12 : hour % 12;

  const nums = stage === "hour"
    ? Array.from({ length: 12 }, (_, i) => i + 1) // 1..12
    : Array.from({ length: 12 }, (_, i) => i * 5); // 0,5,..55

  function pick(n: number) {
    if (stage === "hour") {
      setHour(period === "AM" ? (n === 12 ? 0 : n) : (n === 12 ? 12 : n + 12));
      setStage("minute");
    } else {
      setMinute(n);
    }
  }

  function pickPeriod(p: "AM" | "PM") {
    if (p === period) return;
    setHour((prev) => (p === "PM" ? prev + 12 : prev - 12));
  }

  // Tanlangan qiymatning strelka burchagini hisoblash
  const activeIdx = stage === "hour"
    ? (displayHour === 12 ? 11 : displayHour - 1)
    : Math.round(minute / 5) % 12;

  const pad = (n: number) => String(n).padStart(2, "0");

  return (
    <div className="clock-overlay" onClick={onCancel}>
      <div className="clock-modal" onClick={(e) => e.stopPropagation()}>
        <div className="clock-modal__head">
          <div className="clock-modal__time">
            <span
              className={`clock-modal__seg${stage === "hour" ? " active" : ""}`}
              onClick={() => setStage("hour")}
            >
              {pad(displayHour)}
            </span>
            <span> : </span>
            <span
              className={`clock-modal__seg${stage === "minute" ? " active" : ""}`}
              onClick={() => setStage("minute")}
            >
              {pad(minute)}
            </span>
          </div>
          <div className="clock-modal__ampm">
            <button
              type="button"
              className={`clock-modal__ampm-btn${period === "AM" ? " active" : ""}`}
              onClick={() => pickPeriod("AM")}
            >
              AM
            </button>
            <button
              type="button"
              className={`clock-modal__ampm-btn${period === "PM" ? " active" : ""}`}
              onClick={() => pickPeriod("PM")}
            >
              PM
            </button>
          </div>
        </div>
        <div className="clock-modal__label">
          {stage === "hour" ? "Soatni tanlang" : "Daqiqani tanlang"}
        </div>

        <div className="clock-face">
          {/* strelka */}
          <ClockHand idx={activeIdx} />
          {nums.map((n, i) => {
            const angle = (i * 30 - 90) * (Math.PI / 180);
            const x = CENTER + R * Math.cos(angle);
            const y = CENTER + R * Math.sin(angle);
            const isActive = stage === "hour"
              ? (displayHour === n)
              : (minute === n);
            return (
              <div
                key={n}
                className={`clock-num${isActive ? " active" : ""}`}
                style={{ left: x, top: y }}
                onClick={() => pick(n)}
              >
                {stage === "hour" ? n : pad(n)}
              </div>
            );
          })}
        </div>

        <div className="clock-modal__foot">
          <button className="btn btn--ghost" onClick={onCancel}>Bekor</button>
          <button className="btn btn--primary" onClick={() => onConfirm(`${pad(hour)}:${pad(minute)}`)}>
            Tayyor
          </button>
        </div>
      </div>
    </div>
  );
}

function ClockHand({ idx }: { idx: number }) {
  const angle = idx * 30 - 90;
  const rad = angle * (Math.PI / 180);
  const x = CENTER + R * Math.cos(rad);
  const y = CENTER + R * Math.sin(rad);
  return (
    <svg className="clock-hand" width="220" height="220" style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      <circle cx={CENTER} cy={CENTER} r="4" fill="var(--accent)" />
      <line x1={CENTER} y1={CENTER} x2={x} y2={y} stroke="var(--accent)" strokeWidth="2" />
    </svg>
  );
}

import { useEffect, useState } from "react";
import { progressColor } from "../../utils/progress";

interface Props {
  value: number;
  editable: boolean;
  onCommit: (value: number) => void;
  label?: string;
}

export function ProgressSlider({ value, editable, onCommit, label = "Bajarilish darajasi" }: Props) {
  const [local, setLocal] = useState(value);

  useEffect(() => {
    setLocal(value);
  }, [value]);

  function commit() {
    if (local !== value) onCommit(local);
  }

  return (
    <div className="progress-slider">
      <div className="progress-slider__head">
        <span>{label}</span>
        <span className="progress-slider__pct" style={{ color: progressColor(local) }}>
          {local}%
        </span>
      </div>
      {editable ? (
        <input
          type="range"
          min={0}
          max={100}
          step={5}
          value={local}
          onChange={(e) => setLocal(Number(e.target.value))}
          onMouseUp={commit}
          onTouchEnd={commit}
          onKeyUp={commit}
          className="progress-slider__input"
          style={{
            color: progressColor(local),
            background: `linear-gradient(to right, ${progressColor(local)} ${local}%, var(--surface) ${local}%)`,
          }}
        />
      ) : (
        <div className="progress-bar">
          <div
            className="progress-bar__fill"
            style={{ width: `${value}%`, background: progressColor(value) }}
          />
        </div>
      )}
    </div>
  );
}

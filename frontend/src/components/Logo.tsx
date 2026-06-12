import { useEffect, useState } from "react";
import { brandingApi } from "../api/client";

/**
 * Brend logo. Sozlamalarda yuklangan logotipni ko'rsatadi (yoki /logo.png),
 * topilmasa — SVG "IQTM" wordmark (brend gradient) ko'rsatadi.
 */
export function Logo() {
  const [imgOk, setImgOk] = useState(true);
  const [src, setSrc] = useState("/logo.png");
  const [size, setSize] = useState(30);

  useEffect(() => {
    brandingApi
      .get()
      .then((b) => {
        setSrc(b.logo_path || "/logo.png");
        setSize(b.logo_size || 30);
      })
      .catch(() => {});
  }, []);

  if (imgOk) {
    return (
      <img
        src={src}
        alt="IQTM"
        className="brand-logo"
        style={{ height: size }}
        onError={() => setImgOk(false)}
      />
    );
  }

  return (
    <svg className="brand-logo" style={{ height: size }} viewBox="0 0 168 40" role="img" aria-label="IQTM">
      <defs>
        <linearGradient id="iqtm-g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#1b3b6f" />
          <stop offset="55%" stopColor="#2a8fd8" />
          <stop offset="100%" stopColor="#4caf50" />
        </linearGradient>
      </defs>
      <text
        x="0"
        y="31"
        fontFamily="-apple-system, Segoe UI, Roboto, sans-serif"
        fontSize="32"
        fontWeight="800"
        letterSpacing="1"
        fill="url(#iqtm-g)"
      >
        IQTM
      </text>
    </svg>
  );
}

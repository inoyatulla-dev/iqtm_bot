// Telegram WebApp bilan ishlash — bitta joyda jamlangan.
// Telegram ichida `window.Telegram.WebApp` mavjud bo'ladi.
// Dev (oddiy brauzer) uchun VITE_DEV_INIT_DATA fallback.

interface TgWebApp {
  initData: string;
  initDataUnsafe: {
    user?: { id: number; first_name: string; last_name?: string; username?: string; language_code?: string };
  };
  ready: () => void;
  expand: () => void;
  close: () => void;
  setHeaderColor?: (color: string) => void;
  setBackgroundColor?: (color: string) => void;
  openTelegramLink?: (url: string) => void;
  openLink?: (url: string) => void;
  HapticFeedback?: { impactOccurred: (s: string) => void };
}

declare global {
  interface Window {
    Telegram?: { WebApp: TgWebApp };
  }
}

export const tg = window.Telegram?.WebApp;

// Ilovaning doimiy fon rangi (index.css dagi --secondary-bg bilan mos)
const FIXED_BG_COLOR = "#0f172a";

export function initTelegram() {
  if (tg) {
    tg.ready();
    tg.expand();
    try {
      tg.setHeaderColor?.(FIXED_BG_COLOR);
      tg.setBackgroundColor?.(FIXED_BG_COLOR);
    } catch {
      // eski Telegram versiyalari bu metodlarni qo'llamasligi mumkin
    }
  }
}

// Bot username (taklif havolasi uchun)
export const BOT_USERNAME = "iqtm_bot";

export function inviteLink(): string {
  return `https://t.me/${BOT_USERNAME}`;
}

/** Taklif havolasini Telegram orqali ulashish (chat tanlash oynasi). */
export function shareInvite(text = "IQTM Workspace ilovasiga taklif") {
  const url = inviteLink();
  const shareUrl =
    "https://t.me/share/url?url=" +
    encodeURIComponent(url) +
    "&text=" +
    encodeURIComponent(text);
  if (tg?.openTelegramLink) {
    tg.openTelegramLink(shareUrl);
  } else {
    window.open(shareUrl, "_blank");
  }
}

export function copyText(text: string): Promise<boolean> {
  if (navigator.clipboard) {
    return navigator.clipboard.writeText(text).then(
      () => true,
      () => false
    );
  }
  return Promise.resolve(false);
}

export function getInitData(): string {
  if (tg?.initData) return tg.initData;
  // Dev fallback (faqat `vite dev` rejimida — production buildga kirmaydi)
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_DEV_INIT_DATA || "";
  }
  return "";
}

export function haptic() {
  tg?.HapticFeedback?.impactOccurred("light");
}

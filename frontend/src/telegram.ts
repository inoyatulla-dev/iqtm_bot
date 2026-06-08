// Telegram WebApp bilan ishlash — bitta joyda jamlangan.
// Telegram ichida `window.Telegram.WebApp` mavjud bo'ladi.
// Dev (oddiy brauzer) uchun VITE_DEV_INIT_DATA fallback.

interface TgWebApp {
  initData: string;
  initDataUnsafe: {
    user?: { id: number; first_name: string; last_name?: string; username?: string; language_code?: string };
  };
  colorScheme: "light" | "dark";
  themeParams: Record<string, string>;
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

export function initTelegram() {
  if (tg) {
    tg.ready();
    tg.expand();
    try {
      tg.setHeaderColor?.("secondary_bg_color");
      tg.setBackgroundColor?.("secondary_bg_color");
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
  // Dev fallback (brauzerda sinash uchun)
  return import.meta.env.VITE_DEV_INIT_DATA || "";
}

export function getColorScheme(): "light" | "dark" {
  return tg?.colorScheme || "light";
}

export function haptic() {
  tg?.HapticFeedback?.impactOccurred("light");
}

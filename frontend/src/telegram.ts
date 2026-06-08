// Telegram WebApp bilan ishlash — bitta joyda jamlangan.
// Telegram ichida `window.Telegram.WebApp` mavjud bo'ladi.
// Dev (oddiy brauzer) uchun VITE_DEV_INIT_DATA fallback.

interface TgWebApp {
  initData: string;
  initDataUnsafe: { user?: { id: number; first_name: string; username?: string } };
  colorScheme: "light" | "dark";
  themeParams: Record<string, string>;
  ready: () => void;
  expand: () => void;
  close: () => void;
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
  }
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

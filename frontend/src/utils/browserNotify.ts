/** Brauzer bildirishnomasi uchun ruxsat so'raydi (bir marta, foydalanuvchi hali qaror qilmagan bo'lsa). */
export function requestNotificationPermission() {
  if (typeof Notification === "undefined") return;
  if (Notification.permission === "default") {
    Notification.requestPermission().catch(() => {});
  }
}

/** Tizim darajasidagi (OS) brauzer bildirishnomasini ko'rsatadi, agar ruxsat berilgan bo'lsa. */
export function showBrowserNotification(title: string, body: string, onClick?: () => void) {
  if (typeof Notification === "undefined") return;
  if (Notification.permission !== "granted") return;
  try {
    const n = new Notification(title, { body, icon: "/logo.png" });
    n.onclick = () => {
      window.focus();
      onClick?.();
      n.close();
    };
  } catch {
    /* jim */
  }
}

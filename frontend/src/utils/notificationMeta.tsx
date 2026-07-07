import {
  AlertTriangle, Bell, CheckCircle2, ClipboardList, MessageSquare, RefreshCw,
} from "lucide-react";
import type { AppNotification } from "../api/types";

export type NotifIconType = typeof Bell;

export const NOTIF_TYPE_META: Record<string, { title: string; icon: NotifIconType; cls: string }> = {
  task_assigned: { title: "Yangi vazifa tayinlandi", icon: ClipboardList, cls: "accent" },
  status_change: { title: "Vazifa holati o'zgardi", icon: RefreshCw, cls: "accent" },
  done: { title: "Vazifa tasdiqlandi", icon: CheckCircle2, cls: "ok" },
  comment: { title: "Yangi izoh", icon: MessageSquare, cls: "accent2" },
  reminder: { title: "Vazifa muddati yaqinlashmoqda", icon: AlertTriangle, cls: "danger" },
};
export const DEFAULT_NOTIF_META = { title: "Bildirishnoma", icon: Bell, cls: "accent" };

export function notifTitle(type: string): string {
  return (NOTIF_TYPE_META[type] ?? DEFAULT_NOTIF_META).title;
}

export function stripHtml(s: string): string {
  return s.replace(/<[^>]+>/g, "");
}

/** Qatordagi yetakchi emoji-belgilarni olib tashlaydi (harf/raqamgacha). */
function stripLeadingEmoji(line: string): string {
  let s = line.trim();
  for (;;) {
    const m = /^(\S+)\s+(.*)$/.exec(s);
    if (!m) break;
    if (/[\p{L}\p{N}]/u.test(m[1])) break;
    s = m[2];
  }
  return s;
}

/** Xabar matnini bitta ixcham tavsif qatoriga birlashtiradi (birinchi — sarlavha
 * qatori — tashlab yuboriladi, chunki u sarlavhada alohida ko'rsatiladi). */
export function summarizeNotification(n: AppNotification): string {
  const lines = stripHtml(n.text).split("\n").map((l) => l.trim()).filter(Boolean);
  return lines.slice(1).map(stripLeadingEmoji).filter(Boolean).join(" · ");
}

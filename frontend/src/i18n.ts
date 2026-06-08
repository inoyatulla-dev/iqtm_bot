import {
  createContext, createElement, useContext, type ReactNode,
} from "react";

export type Lang = "uz" | "ru" | "en";

export const LANGS: { code: Lang; label: string; flag: string }[] = [
  { code: "uz", label: "O'zbekcha", flag: "🇺🇿" },
  { code: "ru", label: "Русский", flag: "🇷🇺" },
  { code: "en", label: "English", flag: "🇬🇧" },
];

type Dict = Record<string, string>;

const uz: Dict = {
  "app.name": "IQTM Workspace",
  "common.loading": "Yuklanmoqda…",
  "common.error": "Xatolik",
  "common.retry": "Qayta urinish",
  "common.close": "Yopish",
  "common.cancel": "Bekor qilish",
  "common.save": "Saqlash",
  "common.saved": "✅ Saqlandi",
  "common.delete": "O'chirish",

  "tabs.board": "Doska",
  "tabs.users": "Xodimlar",
  "tabs.departments": "Bo'limlar",
  "tabs.stats": "Statistika",
  "tabs.settings": "Sozlama",

  "status.new": "Yangi",
  "status.in_progress": "Jarayonda",
  "status.review": "Tekshiruvda",
  "status.done": "Bajarildi",
  "role.boss": "Admin",
  "role.worker": "Xodim",

  "board.empty": "Bo'sh",

  "task.new": "Yangi vazifa",
  "task.name": "Nomi",
  "task.namePh": "Vazifa nomi",
  "task.desc": "Tavsif",
  "task.descPh": "Ixtiyoriy",
  "task.dept": "Bo'lim",
  "task.unassigned": "— tanlanmagan —",
  "task.masul": "Mas'ul xodim",
  "task.deadline": "Muddat",
  "task.delete": "🗑 O'chirish",
  "task.confirmDelete": "🗑 Rostdan o'chirilsinmi? (bosing)",
  "task.nameErr": "Nom kamida 3 harf bo'lsin",
  "task.saving": "Saqlanmoqda…",

  "users.invite": "➕ Xodim taklif qilish",
  "users.inviteTitle": "Xodim taklif qilish",
  "users.inviteSub": "Havolani yuboring — xodim botni ochib ariza qoldiradi, keyin uni tasdiqlaysiz",
  "users.share": "📤 Telegram orqali ulashish",
  "users.copy": "📋 Nusxalash",
  "users.copied": "✅ Nusxalandi",
  "users.linkLabel": "Taklif havolasi",
  "users.pending": "🔔 Yangi arizalar",
  "users.list": "👥 Xodimlar",
  "users.makeAdmin": "Admin qilish",
  "users.makeWorker": "Xodim qilish",
  "users.assignDept": "Bo'lim biriktirish",
  "users.block": "Bloklash",
  "users.unblock": "Blokdan chiqarish",
  "users.delete": "O'chirish",
  "users.confirmDelTitle": "O'chirishni tasdiqlang",
  "users.confirmDelBtn": "🗑 Ha, o'chirish",
  "users.noDept": "Bo'limsiz",
  "users.blocked": "blok",
  "users.approve": "Tasdiqlash",

  "dept.add": "➕ Bo'lim qo'shish",
  "dept.list": "🏢 Bo'limlar",
  "dept.newTitle": "Yangi bo'lim",
  "dept.editTitle": "Bo'limni tahrirlash",
  "dept.codeLabel": "Kod (lotin, masalan: it)",
  "dept.name": "Nomi",
  "dept.emoji": "Emoji",
  "dept.color": "Rang",
  "dept.codeErr": "Kod: 2-10 ta kichik harf/raqam",
  "dept.nameErr": "Nom kamida 2 harf",

  "stats.titleGlobal": "📊 Umumiy statistika",
  "stats.titleMy": "📊 Mening statistikam",
  "stats.total": "Jami",
  "stats.overdue": "Kechikkan",
  "stats.rating": "🏆 Xodimlar reytingi",

  "settings.group": "📡 Guruh",
  "settings.groupId": "Guruh chat ID (manfiy, -100…)",
  "settings.groupHint": "💡 Guruhga botni admin qiling va guruhda /set_group yuboring — ID avtomatik aniqlanadi.",
  "settings.topics": "🧵 Umumiy mavzular (topic ID)",
  "settings.topicTasks": "📋 Vazifalar mavzusi",
  "settings.topicReports": "📊 Hisobotlar mavzusi",
  "settings.deptTopics": "🏢 Bo'lim mavzulari",
  "settings.deptTopicsSave": "Bo'lim mavzularini saqlash",
  "settings.admins": "👑 Adminlar",
  "settings.adminsHint": "Bir nechta admin bo'lishi mumkin. Xodimni tanlab \"Admin qilish\" orqali tayinlang.",
  "settings.language": "🌐 Til",

  "register.title": "Ro'yxatdan o'tish",
  "register.subtitle": "Ism va familiyangizni kiriting — admin tasdiqlaydi.",
  "register.firstName": "Ism",
  "register.lastName": "Familiya",
  "register.submit": "Yuborish",
  "register.submitting": "Yuborilmoqda…",
  "register.sentTitle": "✅ Ariza yuborildi",
  "register.sentMsg": "Admin tasdiqlagunicha kuting. Tasdiqlangach, ilovani qayta oching.",
  "register.checkStatus": "Holatni tekshirish",
  "register.nameErr": "Ismingizni kiriting",

  "blocked.title": "🚫 Bloklangan",
  "blocked.msg": "Kirishingiz cheklangan.",
};

const ru: Dict = {
  "app.name": "IQTM Workspace",
  "common.loading": "Загрузка…",
  "common.error": "Ошибка",
  "common.retry": "Повторить",
  "common.close": "Закрыть",
  "common.cancel": "Отмена",
  "common.save": "Сохранить",
  "common.saved": "✅ Сохранено",
  "common.delete": "Удалить",

  "tabs.board": "Доска",
  "tabs.users": "Сотрудники",
  "tabs.departments": "Отделы",
  "tabs.stats": "Статистика",
  "tabs.settings": "Настройки",

  "status.new": "Новые",
  "status.in_progress": "В работе",
  "status.review": "На проверке",
  "status.done": "Готово",
  "role.boss": "Админ",
  "role.worker": "Сотрудник",

  "board.empty": "Пусто",

  "task.new": "Новая задача",
  "task.name": "Название",
  "task.namePh": "Название задачи",
  "task.desc": "Описание",
  "task.descPh": "Необязательно",
  "task.dept": "Отдел",
  "task.unassigned": "— не выбрано —",
  "task.masul": "Ответственный",
  "task.deadline": "Срок",
  "task.delete": "🗑 Удалить",
  "task.confirmDelete": "🗑 Точно удалить? (нажмите)",
  "task.nameErr": "Название минимум 3 символа",
  "task.saving": "Сохранение…",

  "users.invite": "➕ Пригласить сотрудника",
  "users.inviteTitle": "Пригласить сотрудника",
  "users.inviteSub": "Отправьте ссылку — сотрудник откроет бота и подаст заявку, затем вы подтвердите",
  "users.share": "📤 Поделиться в Telegram",
  "users.copy": "📋 Копировать",
  "users.copied": "✅ Скопировано",
  "users.linkLabel": "Ссылка-приглашение",
  "users.pending": "🔔 Новые заявки",
  "users.list": "👥 Сотрудники",
  "users.makeAdmin": "Сделать админом",
  "users.makeWorker": "Сделать сотрудником",
  "users.assignDept": "Назначить отдел",
  "users.block": "Заблокировать",
  "users.unblock": "Разблокировать",
  "users.delete": "Удалить",
  "users.confirmDelTitle": "Подтвердите удаление",
  "users.confirmDelBtn": "🗑 Да, удалить",
  "users.noDept": "Без отдела",
  "users.blocked": "блок",
  "users.approve": "Подтвердить",

  "dept.add": "➕ Добавить отдел",
  "dept.list": "🏢 Отделы",
  "dept.newTitle": "Новый отдел",
  "dept.editTitle": "Редактировать отдел",
  "dept.codeLabel": "Код (латиница, напр: it)",
  "dept.name": "Название",
  "dept.emoji": "Эмодзи",
  "dept.color": "Цвет",
  "dept.codeErr": "Код: 2-10 строчных букв/цифр",
  "dept.nameErr": "Название минимум 2 символа",

  "stats.titleGlobal": "📊 Общая статистика",
  "stats.titleMy": "📊 Моя статистика",
  "stats.total": "Всего",
  "stats.overdue": "Просрочено",
  "stats.rating": "🏆 Рейтинг сотрудников",

  "settings.group": "📡 Группа",
  "settings.groupId": "ID чата группы (отрицательный, -100…)",
  "settings.groupHint": "💡 Добавьте бота админом в группу и отправьте /set_group — ID определится автоматически.",
  "settings.topics": "🧵 Общие темы (topic ID)",
  "settings.topicTasks": "📋 Тема для задач",
  "settings.topicReports": "📊 Тема для отчётов",
  "settings.deptTopics": "🏢 Темы отделов",
  "settings.deptTopicsSave": "Сохранить темы отделов",
  "settings.admins": "👑 Админы",
  "settings.adminsHint": "Может быть несколько админов. Выберите сотрудника и нажмите «Сделать админом».",
  "settings.language": "🌐 Язык",

  "register.title": "Регистрация",
  "register.subtitle": "Введите имя и фамилию — админ подтвердит.",
  "register.firstName": "Имя",
  "register.lastName": "Фамилия",
  "register.submit": "Отправить",
  "register.submitting": "Отправка…",
  "register.sentTitle": "✅ Заявка отправлена",
  "register.sentMsg": "Дождитесь подтверждения админа, затем откройте приложение снова.",
  "register.checkStatus": "Проверить статус",
  "register.nameErr": "Введите имя",

  "blocked.title": "🚫 Заблокировано",
  "blocked.msg": "Доступ ограничен.",
};

const en: Dict = {
  "app.name": "IQTM Workspace",
  "common.loading": "Loading…",
  "common.error": "Error",
  "common.retry": "Retry",
  "common.close": "Close",
  "common.cancel": "Cancel",
  "common.save": "Save",
  "common.saved": "✅ Saved",
  "common.delete": "Delete",

  "tabs.board": "Board",
  "tabs.users": "Staff",
  "tabs.departments": "Departments",
  "tabs.stats": "Stats",
  "tabs.settings": "Settings",

  "status.new": "New",
  "status.in_progress": "In progress",
  "status.review": "Review",
  "status.done": "Done",
  "role.boss": "Admin",
  "role.worker": "Worker",

  "board.empty": "Empty",

  "task.new": "New task",
  "task.name": "Name",
  "task.namePh": "Task name",
  "task.desc": "Description",
  "task.descPh": "Optional",
  "task.dept": "Department",
  "task.unassigned": "— none —",
  "task.masul": "Assignee",
  "task.deadline": "Deadline",
  "task.delete": "🗑 Delete",
  "task.confirmDelete": "🗑 Really delete? (tap)",
  "task.nameErr": "Name at least 3 characters",
  "task.saving": "Saving…",

  "users.invite": "➕ Invite employee",
  "users.inviteTitle": "Invite employee",
  "users.inviteSub": "Send the link — the employee opens the bot and applies, then you approve",
  "users.share": "📤 Share via Telegram",
  "users.copy": "📋 Copy",
  "users.copied": "✅ Copied",
  "users.linkLabel": "Invite link",
  "users.pending": "🔔 New requests",
  "users.list": "👥 Staff",
  "users.makeAdmin": "Make admin",
  "users.makeWorker": "Make worker",
  "users.assignDept": "Assign department",
  "users.block": "Block",
  "users.unblock": "Unblock",
  "users.delete": "Delete",
  "users.confirmDelTitle": "Confirm deletion",
  "users.confirmDelBtn": "🗑 Yes, delete",
  "users.noDept": "No department",
  "users.blocked": "blocked",
  "users.approve": "Approve",

  "dept.add": "➕ Add department",
  "dept.list": "🏢 Departments",
  "dept.newTitle": "New department",
  "dept.editTitle": "Edit department",
  "dept.codeLabel": "Code (latin, e.g: it)",
  "dept.name": "Name",
  "dept.emoji": "Emoji",
  "dept.color": "Color",
  "dept.codeErr": "Code: 2-10 lowercase letters/digits",
  "dept.nameErr": "Name at least 2 characters",

  "stats.titleGlobal": "📊 Overall statistics",
  "stats.titleMy": "📊 My statistics",
  "stats.total": "Total",
  "stats.overdue": "Overdue",
  "stats.rating": "🏆 Staff rating",

  "settings.group": "📡 Group",
  "settings.groupId": "Group chat ID (negative, -100…)",
  "settings.groupHint": "💡 Add the bot as admin to the group and send /set_group — the ID is detected automatically.",
  "settings.topics": "🧵 General topics (topic ID)",
  "settings.topicTasks": "📋 Tasks topic",
  "settings.topicReports": "📊 Reports topic",
  "settings.deptTopics": "🏢 Department topics",
  "settings.deptTopicsSave": "Save department topics",
  "settings.admins": "👑 Admins",
  "settings.adminsHint": "There can be several admins. Pick an employee and tap “Make admin”.",
  "settings.language": "🌐 Language",

  "register.title": "Registration",
  "register.subtitle": "Enter your first and last name — admin will approve.",
  "register.firstName": "First name",
  "register.lastName": "Last name",
  "register.submit": "Submit",
  "register.submitting": "Submitting…",
  "register.sentTitle": "✅ Request sent",
  "register.sentMsg": "Wait for admin approval, then reopen the app.",
  "register.checkStatus": "Check status",
  "register.nameErr": "Enter your name",

  "blocked.title": "🚫 Blocked",
  "blocked.msg": "Your access is restricted.",
};

const DICTS: Record<Lang, Dict> = { uz, ru, en };

export function translate(lang: Lang, key: string): string {
  return DICTS[lang]?.[key] ?? uz[key] ?? key;
}

interface I18nCtx {
  lang: Lang;
  t: (key: string) => string;
  setLang: (l: Lang) => void;
}

export const I18nContext = createContext<I18nCtx>({
  lang: "uz",
  t: (k) => translate("uz", k),
  setLang: () => {},
});

export const useI18n = () => useContext(I18nContext);

export function I18nProvider({
  lang,
  setLang,
  children,
}: {
  lang: Lang;
  setLang: (l: Lang) => void;
  children: ReactNode;
}) {
  const t = (key: string) => translate(lang, key);
  return createElement(I18nContext.Provider, { value: { lang, t, setLang } }, children);
}

import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

import db
from scheduler import setup_scheduler

from handlers.common import (
    start, menu_command, menu_callback, help_command,
    set_group_command, topic_detect_command,
    task_menu, proj_menu, group_settings_menu, stats_menu, bot_settings_menu,
)
from handlers.users import (
    user_list, user_view, user_block, user_unblock,
    user_del_confirm, user_del, my_workers,
    get_user_add_conv, get_user_edit_conv,
)
from handlers.departments import (
    dep_list, dep_view, dep_set_admin, dep_admin_set,
    dep_del_confirm, dep_del,
    get_dep_add_conv, get_dep_edit_conv, get_dep_set_topic_conv,
)
from handlers.tasks import (
    dep_tasks, my_tasks, task_view,
    task_done, task_del_confirm, task_del,
    task_dep_done, task_dep_assign, task_dep_assign_save,
    task_status_menu, task_set_status,
    td_status_menu, td_set_status,
    get_task_create_conv, get_task_edit_conv, get_reminder_conv,
    get_personal_task_conv,
)
from handlers.projects import (
    proj_list, proj_view, proj_stages_view, stage_view,
    stage_done, proj_del_confirm, proj_del,
    proj_status_menu, proj_set_status,
    get_proj_create_conv, get_stage_add_conv, get_stage_edit_conv,
)
from handlers.stats import (
    stats_global, stats_dep, stats_personal,
    rating_global, rating_dep, report_weekly, report_weekly_send, report_dep,
)
from handlers.superadmin import (
    role_manage, role_view_by_type, user_setrole_start, user_setrole, settings, settings_group,
    backup_db, super_code_handler,
    pending_list, approve_user_start, approve_role, approve_dep, reject_user,
    group_members, gm_add, gm_role, gm_dep,
    link_topic, link_group_topic, topic_settings, topic_auto_help,
    get_topic_set_conv, invite_link,
)

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")


async def error_handler(update: object, context) -> None:
    logger.error("Update %s da xato: %s", update, context.error, exc_info=context.error)


async def noop_callback(update: Update, context) -> None:
    """Bo'sh tugma — hech narsa qilmaydi."""
    if update.callback_query:
        await context.bot.answer_callback_query(update.callback_query.id)


async def post_init(application: Application) -> None:
    await db.init_db()
    await db.seed_data()
    scheduler = setup_scheduler(application.bot)
    scheduler.start()
    application.bot_data["scheduler"] = scheduler
    logger.info("Bot ishga tushdi. DB va scheduler tayyorlandi.")


async def post_shutdown(application: Application) -> None:
    scheduler = application.bot_data.get("scheduler")
    if scheduler and scheduler.running:
        scheduler.shutdown()


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN .env faylida ko'rsatilmagan!")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # ── Error handler ─────────────────────────────────────────────
    app.add_error_handler(error_handler)

    # ── Conversations (eng avval) ─────────────────────────────────
    app.add_handler(get_topic_set_conv())
    app.add_handler(get_user_add_conv())
    app.add_handler(get_user_edit_conv())
    app.add_handler(get_dep_add_conv())
    app.add_handler(get_dep_edit_conv())
    app.add_handler(get_dep_set_topic_conv())
    app.add_handler(get_personal_task_conv())
    app.add_handler(get_task_create_conv())
    app.add_handler(get_task_edit_conv())
    app.add_handler(get_reminder_conv())
    app.add_handler(get_proj_create_conv())
    app.add_handler(get_stage_add_conv())
    app.add_handler(get_stage_edit_conv())

    # ── Commands ──────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("yordam", help_command))
    app.add_handler(CommandHandler("set_group", set_group_command))
    app.add_handler(CommandHandler("topic_aniqla", topic_detect_command))

    # ── Callback Queries ──────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(noop_callback, pattern="^noop$"))
    app.add_handler(CallbackQueryHandler(noop_callback, pattern="^cal_ignore$"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))

    # Sub-menyular
    app.add_handler(CallbackQueryHandler(task_menu,          pattern="^task_menu$"))
    app.add_handler(CallbackQueryHandler(proj_menu,          pattern="^proj_menu$"))
    app.add_handler(CallbackQueryHandler(group_settings_menu, pattern="^group_settings_menu$"))
    app.add_handler(CallbackQueryHandler(stats_menu,         pattern="^stats_menu$"))
    app.add_handler(CallbackQueryHandler(bot_settings_menu,  pattern="^bot_settings_menu$"))

    # Users
    app.add_handler(CallbackQueryHandler(user_list, pattern="^user_list$"))
    app.add_handler(CallbackQueryHandler(user_view, pattern="^user_view:"))
    app.add_handler(CallbackQueryHandler(user_setrole_start, pattern="^user_role:"))
    app.add_handler(CallbackQueryHandler(user_setrole, pattern="^user_setrole:"))
    app.add_handler(CallbackQueryHandler(user_block, pattern="^user_block:"))
    app.add_handler(CallbackQueryHandler(user_unblock, pattern="^user_unblock:"))
    app.add_handler(CallbackQueryHandler(user_del_confirm, pattern="^user_del_confirm:"))
    app.add_handler(CallbackQueryHandler(user_del, pattern="^user_del:"))
    app.add_handler(CallbackQueryHandler(my_workers, pattern="^my_workers$"))

    # Role manage
    app.add_handler(CallbackQueryHandler(role_manage, pattern="^role_manage$"))
    app.add_handler(CallbackQueryHandler(role_view_by_type, pattern="^role_users:"))

    # Pending users
    app.add_handler(CallbackQueryHandler(pending_list, pattern="^pending_list$"))
    app.add_handler(CallbackQueryHandler(approve_user_start, pattern="^approve_user:"))
    app.add_handler(CallbackQueryHandler(approve_role, pattern="^approve_role:"))
    app.add_handler(CallbackQueryHandler(approve_dep, pattern="^approve_dep:"))
    app.add_handler(CallbackQueryHandler(reject_user, pattern="^reject_user:"))

    # Group members
    app.add_handler(CallbackQueryHandler(group_members, pattern="^group_members$"))
    app.add_handler(CallbackQueryHandler(invite_link, pattern="^invite_link$"))
    app.add_handler(CallbackQueryHandler(gm_add, pattern="^gm_add:"))
    app.add_handler(CallbackQueryHandler(gm_role, pattern="^gm_role:"))
    app.add_handler(CallbackQueryHandler(gm_dep, pattern="^gm_dep:"))

    # Departments
    app.add_handler(CallbackQueryHandler(dep_list, pattern="^dep_list$"))
    app.add_handler(CallbackQueryHandler(dep_view, pattern="^dep_view:"))
    app.add_handler(CallbackQueryHandler(dep_set_admin, pattern="^dep_set_admin:"))
    app.add_handler(CallbackQueryHandler(dep_admin_set, pattern="^dep_admin_set:"))
    app.add_handler(CallbackQueryHandler(dep_del_confirm, pattern="^dep_del_confirm:"))
    app.add_handler(CallbackQueryHandler(dep_del, pattern="^dep_del:"))

    # Tasks
    app.add_handler(CallbackQueryHandler(dep_tasks, pattern="^dep_tasks(:.+)?$"))
    app.add_handler(CallbackQueryHandler(my_tasks, pattern="^my_tasks(:.+)?$"))
    app.add_handler(CallbackQueryHandler(task_view, pattern="^task_view:"))
    app.add_handler(CallbackQueryHandler(task_done, pattern="^task_done:"))
    app.add_handler(CallbackQueryHandler(task_del_confirm, pattern="^task_del_confirm:"))
    app.add_handler(CallbackQueryHandler(task_del, pattern="^task_del:"))
    app.add_handler(CallbackQueryHandler(task_dep_done, pattern="^td_done:"))
    app.add_handler(CallbackQueryHandler(task_dep_assign, pattern="^td_assign:"))
    app.add_handler(CallbackQueryHandler(task_dep_assign_save, pattern="^td_worker:"))
    app.add_handler(CallbackQueryHandler(task_status_menu, pattern="^task_status_menu:"))
    app.add_handler(CallbackQueryHandler(task_set_status, pattern="^task_setstatus:"))
    app.add_handler(CallbackQueryHandler(td_status_menu, pattern="^td_status_menu:"))
    app.add_handler(CallbackQueryHandler(td_set_status, pattern="^td_setstatus:"))

    # Projects
    app.add_handler(CallbackQueryHandler(proj_list, pattern="^proj_list$"))
    app.add_handler(CallbackQueryHandler(proj_list, pattern="^proj_page:"))
    app.add_handler(CallbackQueryHandler(proj_status_menu, pattern="^proj_status_menu:"))
    app.add_handler(CallbackQueryHandler(proj_set_status, pattern="^proj_setstatus:"))
    app.add_handler(CallbackQueryHandler(proj_view, pattern="^proj_view:"))
    app.add_handler(CallbackQueryHandler(proj_stages_view, pattern="^proj_stages:"))
    app.add_handler(CallbackQueryHandler(stage_view, pattern="^stage_view:"))
    app.add_handler(CallbackQueryHandler(stage_done, pattern="^stage_done:"))
    app.add_handler(CallbackQueryHandler(proj_del_confirm, pattern="^proj_del_confirm:"))
    app.add_handler(CallbackQueryHandler(proj_del, pattern="^proj_del:"))

    # Stats
    app.add_handler(CallbackQueryHandler(stats_global, pattern="^stats_global$"))
    app.add_handler(CallbackQueryHandler(stats_dep, pattern="^stats_dep$"))
    app.add_handler(CallbackQueryHandler(stats_personal, pattern="^stats_personal$"))
    app.add_handler(CallbackQueryHandler(rating_global, pattern="^rating_global$"))
    app.add_handler(CallbackQueryHandler(rating_dep, pattern="^rating_dep$"))
    app.add_handler(CallbackQueryHandler(report_weekly, pattern="^report_weekly$"))
    app.add_handler(CallbackQueryHandler(report_weekly_send, pattern="^report_weekly_send$"))
    app.add_handler(CallbackQueryHandler(report_dep, pattern="^report_dep$"))

    # Settings
    app.add_handler(CallbackQueryHandler(settings, pattern="^settings$"))
    app.add_handler(CallbackQueryHandler(settings_group, pattern="^settings_group$"))
    app.add_handler(CallbackQueryHandler(backup_db, pattern="^backup_db$"))
    app.add_handler(CallbackQueryHandler(link_topic, pattern="^link_topic:"))
    app.add_handler(CallbackQueryHandler(link_group_topic, pattern="^link_group_topic:"))
    # Topic sozlash
    app.add_handler(CallbackQueryHandler(topic_settings, pattern="^topic_settings$"))
    app.add_handler(CallbackQueryHandler(topic_auto_help, pattern="^topic_auto_help$"))

    # Super transfer kod — faqat text xabarlar uchun (conversations dan keyin)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, super_code_handler)
    )

    logger.info("IQTM Workspace boti ishga tushmoqda...")
    app.run_polling(
        allowed_updates=[
            "message",
            "callback_query",
            "chat_member",
            "my_chat_member",
        ]
    )


if __name__ == "__main__":
    main()

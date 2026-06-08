from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import db


def role_required(*roles):
    """
    Foydalanuvchi rolini tekshiradi.
    roles: 'super', 'admin', 'worker' (birdan ortiq bo'lishi mumkin)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = (
                update.effective_user.id if update.effective_user else None
            )
            if not user_id:
                return

            user = await db.get_user(user_id)
            if not user or user["status"] != "faol":
                msg = "🚫 Sizga ruxsat berilmagan. Administratorga murojaat qiling."
                if update.callback_query:
                    await update.callback_query.answer(msg, show_alert=True)
                elif update.message:
                    await update.message.reply_text(msg)
                return

            if roles and user["role"] not in roles:
                msg = "🚫 Ruxsat yo'q. Bu amal sizning rolingiz uchun mavjud emas."
                if update.callback_query:
                    await update.callback_query.answer(msg, show_alert=True)
                elif update.message:
                    await update.message.reply_text(msg)
                return

            context.user_data["db_user"] = dict(user)
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator


def any_role(func):
    """Ro'yxatga olingan har qanday foydalanuvchi uchun."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id if update.effective_user else None
        if not user_id:
            return
        user = await db.get_user(user_id)
        if not user or user["status"] != "faol":
            msg = "🚫 Sizga ruxsat berilmagan. Administratorga murojaat qiling."
            if update.callback_query:
                await update.callback_query.answer(msg, show_alert=True)
            elif update.message:
                await update.message.reply_text(msg)
            return
        context.user_data["db_user"] = dict(user)
        return await func(update, context, *args, **kwargs)
    return wrapper

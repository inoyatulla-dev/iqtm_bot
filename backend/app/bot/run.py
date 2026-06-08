"""Bot kirish nuqtasi — polling + scheduler.

Ishga tushirish:  python -m app.bot.run
"""
import logging

from telegram.ext import Application, CommandHandler

from app.bot.handlers import set_group, start
from app.bot.scheduler import setup_scheduler
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def _post_init(app: Application):
    scheduler = setup_scheduler()
    scheduler.start()
    app.bot_data["scheduler"] = scheduler
    logger.info("Bot va scheduler ishga tushdi.")


def main():
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN .env da ko'rsatilmagan!")

    app = (
        Application.builder()
        .token(settings.bot_token)
        .post_init(_post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_group", set_group))

    logger.info("IQTM bot polling boshlandi…")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()

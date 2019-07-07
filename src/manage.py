import pprint
import os
import logging

import import_string

from application.ecommerce_api.moltin_api.moltin import MoltinApiSession, MoltinApi
from application.database import RedisStorage
from application.bot.telegram_bot import TelegramBot
from config import setup_logging

logger = logging.getLogger(__name__)


def main():
    app_config_name = os.getenv('APP_SETTINGS')
    app_config = import_string(app_config_name)

    setup_logging()

    RedisStorage.initialize(**app_config.REDIS_SETTINGS)

    moltin_api_session = MoltinApiSession(
        app_config.MOLTIN_API_URL,
        app_config.MOLTIN_CLIENT_ID,
        app_config.MOLTIN_CLIENT_SECRET
    )
    moltin_api = MoltinApi(moltin_api_session)
    print(moltin_api.get_products())

    telegram_bot = TelegramBot(app_config.TELEGRAM_BOT_TOKEN, moltin_api)
    telegram_bot.start()


if __name__ == '__main__':
    main()

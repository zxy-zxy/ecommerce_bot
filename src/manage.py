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
    # moltin_api.get_products()
    cart_id = '1488'
    moltin_api.add_product_to_cart(cart_id, '66a35ee3-5912-4a86-a508-2887e56e97c9', 5)
    moltin_api.add_product_to_cart(cart_id, 'f3efac3f-0c71-4e12-9ec1-11669ac8fafe', 2)
    print(moltin_api.get_cart(cart_id))
    print(moltin_api.get_cart_products(cart_id))


if __name__ == '__main__':
    main()

# 66a35ee3-5912-4a86-a508-2887e56e97c9
# f3efac3f-0c71-4e12-9ec1-11669ac8fafe

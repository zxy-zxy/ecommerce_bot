import pprint
import os
import logging

from application.ecommerce_api.motlin_api.motlin import MotlinApiSession, MotlinApi
from config import setup_logging

logger = logging.getLogger(__name__)


def main():
    setup_logging()

    api_url = 'https://api.moltin.com'
    client_id = os.getenv('MOLTIN_CLIENT_ID')
    client_secret = os.getenv('MOLTIN_CLIENT_SECRET')

    api_session = MotlinApiSession(api_url, client_id, client_secret)

    motlin = MotlinApi(api_session)
    pprint.pprint(motlin.get_products())


if __name__ == '__main__':
    main()

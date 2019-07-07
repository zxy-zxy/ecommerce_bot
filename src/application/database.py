import logging

import redis

logger = logging.getLogger(__name__)


class RedisStorage:
    connection = None

    @staticmethod
    def initialize(host=None, port=None, url=None):
        logger.debug(
            'Redis instance initialization started, host: {}, port: {}, url: {}'.format(
                host, port, url
            )
        )
        if url:
            RedisStorage.connection = redis.Redis.from_url(url)
        else:
            RedisStorage.connection = redis.Redis(host, port)

    @staticmethod
    def set(key, value):
        return RedisStorage.connection.set(key, value)

    @staticmethod
    def get(key):
        value = RedisStorage.connection.get(key)
        value = value if value is None else value.decode()
        return value

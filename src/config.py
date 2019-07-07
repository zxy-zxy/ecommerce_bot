import os
import logging
import logging.config


def convert_value_to_int(value):
    try:
        return int(value)
    except TypeError:
        return 0


class ConfigError(Exception):
    pass


class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    MOLTIN_API_URL = os.getenv('MOLTIN_API_URL')
    MOLTIN_STORE_ID = os.getenv('MOLTIN_STORE_ID')
    MOLTIN_CLIENT_ID = os.getenv('MOLTIN_CLIENT_ID')
    MOLTIN_CLIENT_SECRET = os.getenv('MOLTIN_CLIENT_SECRET')

    required = [
        'TELEGRAM_BOT_TOKEN',
        'REDIS_SETTINGS',
        'MOLTIN_API_URL',
        'MOLTIN_STORE_ID',
        'MOLTIN_CLIENT_ID',
        'MOLTIN_CLIENT_SECRET'
    ]


class DevelopmentConfig(Config):
    REDIS_SETTINGS = {
        'host': os.getenv('REDIS_HOST'),
        'port': convert_value_to_int(os.getenv('REDIS_PORT')),
        'url': None,
    }


class ProductionConfig(Config):
    REDIS_SETTINGS = {'host': None, 'port': None, 'url': os.getenv('REDIS_URL')}


def setup_logging():
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s — %(name)s — %(levelname)s — %(message)s'
            }
        },
        'handlers': {
            'console': {'class': 'logging.StreamHandler', 'formatter': 'standard'}
        },
        'loggers': {'': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': True}},
    }

    logging.config.dictConfig(logging_config)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)

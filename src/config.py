import logging
import logging.config


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
    logging.getLogger("urllib3").setLevel(logging.WARNING)

LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },
    'loggers': {
        'httpx': {
            'handlers': ['console'],
            'level': 'WARNING',  # This will ignore logs below WARNING level for httpx
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    }
}
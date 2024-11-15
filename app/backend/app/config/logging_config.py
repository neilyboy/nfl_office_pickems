import os
import logging.config
from datetime import datetime

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Define the logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s - %(pathname)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'detailed',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'nfl_pickems.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'auth_file': {
            'level': 'INFO',
            'formatter': 'detailed',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'auth.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        },
        'app.auth': {  # Authentication logger
            'handlers': ['auth_file', 'console'],
            'level': 'INFO',
            'propagate': False
        },
        'app.routes': {  # Routes logger
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

def setup_logging():
    """Initialize logging configuration"""
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info('Logging setup completed')

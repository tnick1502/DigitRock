from version_control.configs import actual_version
import datetime
import logging

time = datetime.datetime.now()
file = f'{time:%d-%m-%Y %H.%M.%S}.log'

class CustomFilter(logging.Filter):

    COLOR = {
        "DEBUG": "GREEN",
        "INFO": "GREEN",
        "WARNING": "YELLOW",
        "ERROR": "RED",
        "CRITICAL": "RED",
    }

    def filter(self, record):
        record.color = CustomFilter.COLOR[record.levelname]
        return True

logger_config = {
    'version': 1,

    # Отключит все логеры, кроме указанных
    'disable_existing_loggers': False,

    'formatters': {
        'std_format': {
            'format': '{asctime} - line: {lineno} - {message}',
            'style': '{'
        }
    },
    'handlers': {
        'stream_handler': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'std_format',
            'filters': ["color_filter"]
        },
        #'file_handler': {
            #'class': 'logging.FileHandler',
            #'level': 'INFO',
            #'formatter': 'std_format',
            #'filename': file
        #}
    },
    'loggers': {
        'app_logger': {
            'level': 'INFO',
            #'handlers': ['stream_handler', 'file_handler'],
            'handlers': ['stream_handler'],

            'propagate': False
        },
        'app_logger.model_logger': {
            'level': 'INFO',
        },
        'app_logger.excel_logger': {
            'level': 'INFO',
        },
    },

    'filters': {
        'color_filter': {
            '()': CustomFilter
        }
    },
    # 'root': {}   # '': {}
    # 'incremental': True
}
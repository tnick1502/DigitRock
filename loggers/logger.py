import logging
import logging.config
from loggers.logger_configs import logger_config

logging.config.dictConfig(logger_config)
app_logger = logging.getLogger("app_logger")
model_logger = logging.getLogger("app_logger.model_logger")
excel_logger = logging.getLogger("app_logger.excel_logger")

"""handler = logging.Handler()
handler.setLevel(logging.INFO)
app_logger.addHandler(handler)
f = logging.Formatter(fmt='%(message)s')
handler.setFormatter(f)"""




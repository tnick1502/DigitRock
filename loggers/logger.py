import logging
import logging.config
from loggers.logger_configs import logger_config

logging.config.dictConfig(logger_config)

app_logger = logging.getLogger("app_logger")
model_logger = logging.getLogger("app_logger.model_logger")
excel_logger = logging.getLogger("app_logger.excel_logger")

def log_this(logger_obj, level: str = "info") -> object:
    """Декоратор для логирования функций и методов
    Аргументы:
        logger_obj - объект логера для записи
        level - уровень записи"""
    def decorator(function):

        decorator.loger = logger_obj
        decorator.log_write = getattr(decorator.loger, level)

        def wrapper(*args, **kwargs):
            try:
                decorator.log_write(f"Вызов функции: {function.__name__}, аргументы: {args, kwargs}")
                function(*args, **kwargs)
                decorator.log_write(f"Вызов функции выполнен успешно")
            except:
                decorator.loger.exception(f"Ошибка в функции {function.__name__}")
        return wrapper

    return decorator

if __name__ == "__main__":

    @log_this(app_logger, "info")
    def f(x):
        return 1/x

    f(1)
    f(0)

    class A:
        def __init__(self, a):
            self.a = a
        @log_this(app_logger, "info")
        def devide(self, x):
            return self.a/x

    a = A(3)
    a.devide(5)
    a.devide(0)


"""handler = logging.Handler()
handler.setLevel(logging.INFO)
app_logger.addHandler(handler)
f = logging.Formatter(fmt='%(message)s')
handler.setFormatter(f)"""




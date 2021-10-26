from loggers.logger import app_logger


def log_this(logger_obj, level: str = "info") -> object:
    """Декоратор для логирования функций и методов
    Аргументы:
        logger_obj - объект логера для записи
        level - уровень записи"""
    def decorator(function):

        decorator.loger = logger_obj
        decorator.log_wite = getattr(decorator.loger, level)

        def wrapper(*args, **kwargs):
            try:
                decorator.log_wite(f"Вызов функции: {function.__name__}, аргументы: {args, kwargs}")
                function(*args, **kwargs)
                decorator.log_wite(f"Вызов функции выполнен успешно")
            except:
                decorator.loger.exception(f"Ошибка в функции {function.__name__}")
        return wrapper

    return decorator


@log_this(app_logger, "info")
def f():
    print("1")

f()


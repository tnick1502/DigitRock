from psycopg2 import connect, errors
import datetime

from metrics.functions import user_ip
from metrics.configs import configs

'''
Пример использования:

@DBCounter("deviator")
def deviator():
    print("t")
'''

def DBCounterDecorator(param_name: str) -> object:
    """Декоратор для записи статистики в базу
    Аргументы:
        param_name - имя параметра для подсчета"""
    def decorator(function):
        decorator.param_name = param_name

        def wrapper(*args, **kwargs):
            with connect(
                    database=configs.DATABASE,
                    user=configs.USER,
                    password=configs.PASSWORD,
                    host=configs.HOST,
                    port=configs.PORT
            ) as conn:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            f"INSERT INTO use_count (user_ip, parameter_name, datetime) VALUES ('{user_ip()}', '{decorator.param_name}', '{datetime.datetime.now()}')"
                        )
                except errors as err:
                    print(err)
                    conn.rollback()
                finally:
                    function(*args, **kwargs)
        return wrapper

    return decorator

def DBCounterFunction(param_name: str):
    with connect(
            database=configs.DATABASE,
            user=configs.USER,
            password=configs.PASSWORD,
            host=configs.HOST,
            port=configs.PORT
    ) as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"INSERT INTO use_count (user_ip, parameter_name, datetime) VALUES ('{user_ip()}', '{param_name}', '{datetime.datetime.now()}')"
                )
        except errors as err:
            print(err)
            conn.rollback()
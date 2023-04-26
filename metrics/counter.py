from psycopg2 import connect, errors
import threading
import datetime

from metrics.functions import user_ip
from metrics.configs import configs
from version_control.configs import actual_version
from singletons import statment

'''
Пример использования:

@DBCounter("deviator")
def deviator():
    print("t")
'''

def DBCounterFunction(param_name: str) -> None:
    try:
        object_number = statment.general_data.object_number
        test_type = statment.general_parameters.test_mode
    except:
        object_number = None
        test_type = None

    def db_write():
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
                        f"INSERT INTO use_count (user_ip, parameter_name, datetime, object_number, test_type, program_version) VALUES ('{user_ip()}', '{param_name}', '{datetime.datetime.now()}','{object_number}', '{test_type}', '{actual_version}')"
                    )
            except (errors, Exception) as err:
                print(err)
                conn.rollback()

    threading.Thread(target=db_write, args=()).start()


if __name__ == "__main__":
    DBCounterFunction("test_2")
from psycopg2 import connect, errors
from threading import Lock
import datetime

from metrics.functions import user_ip
from metrics.configs import configs

class SingletonMeta(type):
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class DBSessionWriter(metaclass=SingletonMeta):
    sheet_load_datetime: datetime.datetime = None
    last_test_save_datetime: datetime.datetime = None

    def set_sheet_load_datetime(self):
        self.sheet_load_datetime = datetime.datetime.now()

    def set_last_test_save_datetime(self):
        self.last_test_save_datetime = datetime.datetime.now()

    def write_session(self, report_count: int, test_type: str, object_number: str):
        if self.sheet_load_datetime:
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
                            f"INSERT INTO sessions (user_ip, session_start, session_end , object_number, test_type, report_count) VALUES ('{user_ip()}', '{self.sheet_load_datetime}', '{datetime.datetime.now()}', '{object_number}', '{test_type}', '{report_count}')"
                        )
                    self.sheet_load_datetime = None
                except errors as err:
                    print(err)
                    conn.rollback()

    def write_test(self, test_type: str, object_number: str):
        if self.sheet_load_datetime:
            with connect(
                    database=configs.DATABASE,
                    user=configs.USER,
                    password=configs.PASSWORD,
                    host=configs.HOST,
                    port=configs.PORT
            ) as conn:
                try:
                    with conn.cursor() as cursor:
                        if not self.last_test_save_datetime:
                            cursor.execute(
                                f"INSERT INTO sessions (user_ip, session_start, session_end , object_number, test_type, report_count) VALUES ('{user_ip()}', '{self.sheet_load_datetime}', '{datetime.datetime.now()}', '{object_number}', '{test_type}', '{1}')"
                            )
                        else:
                            cursor.execute(
                                f"INSERT INTO sessions (user_ip, session_start, session_end , object_number, test_type, report_count) VALUES ('{user_ip()}', '{self.last_test_save_datetime}', '{datetime.datetime.now()}', '{object_number}', '{test_type}', '{1}')"
                            )
                        self.last_test_save_datetime = datetime.datetime.now()
                except errors as err:
                    print(err)
                    conn.rollback()

if __name__ == "__main__":
    session = DBSessionWriter()
    import time
    time.sleep(180)
    session.set_sheet_load_datetime()
    session.write_session(3, 'test', 'test')



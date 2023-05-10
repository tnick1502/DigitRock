import requests
from singletons import statment
from threading import Thread

import warnings

warnings.filterwarnings('ignore')

def control():
    Thread(target=send_request, args=()).start()

def send_request():
    url = 'http://192.168.0.200:8500/reports'

    data = {
        "object_number": statment.general_data.object_number,
        "laboratory_number": statment.current_test,
        "test_type": statment.general_parameters.test_mode,
        "object_name": statment.general_data.object_name,
    }
    try:
        response = requests.post(url=url, json=data)
        assert response.ok, "Не удалось зпаисать"
    except Exception as err:
        print(err)

if __name__=="__main__":
    url = 'http://192.168.0.200:8500/reports'

    data = {
        "object_number": "test",
        "laboratory_number": "test1",
        "test_type": "test",
        "object_name": "test",
    }
    try:
        response = requests.post(url=url, json=data)
        assert response.ok, "Не удалось зпаисать"
    except Exception as err:
        print(err)
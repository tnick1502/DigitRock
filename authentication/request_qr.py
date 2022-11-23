import requests
from singletons import statment
import warnings

warnings.filterwarnings('ignore')

def request_qr():
    with requests.Session() as sess:
        reg = sess.post('https://georeport.ru/authorization/sign-in/',
                        data={
                            "username": "mdgt_admin",
                            "password": "mdgt_admin_password",
                            "grant_type": "password",
                            "scope": "",
                            "client_id": "",
                            "client_secret": ""
                        }, verify=False, allow_redirects=False)

        data = {
            "object_number": statment.general_data.object_number,
            "laboratory_number": statment.current_test,
            "test_type": statment.general_parameters.test_mode,
            "data": {
                "Дата выдачи протокола": statment.general_data.end_date.strftime('%d.%m.%Y')
            },
            "active": True
        }
        response = sess.post('https://georeport.ru/reports/report_and_qr', json=data)
        assert response.ok, "Не удалось сгенерировать код"
        with open("qr.png", "wb") as file:
            file.write(response.content)
        return "qr.png"

if __name__=="__main__":
    with requests.Session() as sess:
        reg = sess.post('https://georeport.ru/authorization/sign-in/',
                        data={
                            "username": "mdgt_admin",
                            "password": "mdgt_admin_password",
                            "grant_type": "password",
                            "scope": "",
                            "client_id": "",
                            "client_secret": ""
                        }, verify=False, allow_redirects=False)

        data = {
            "object_number": "11-547",
            "laboratory_number": "34-ДЛ 5",
            "test_type": "Резонансная колонка",
            "data": {"Дата выдачи протокола": "12.05.2026"},
            "active": True
        }

        response = sess.post('https://georeport.ru/reports/report_and_qr', json=data)
        assert response.ok, "Не удалось сгенерировать код"
        with open("qr.png", "wb") as file:
            file.write(response.content)
import requests

new_show = {
        "laboratory": "mdgt",
        "password": "it_user",

        "test_name": "triaxial",
        "object": "233445",
        "laboratory_number": 12,
        "test_type": "mdgt",

        "data": {
            "Лабораторный номер": "123-ab",
            "Модуль деформации E50, МПа": "15.8",
            "Девиатор разрушения qf, МПа": "1.02"
        }
    }

def request_qr(data):
    response = requests.post('https://georeport.ru/report/', json=data)
    assert response.ok, "Не удалось сгенерировать код"
    with open("qr.png", "wb") as file:
        file.write(response.content)
    return "qr.png"

if __name__=="__main__":
    print(request_qr(new_show))
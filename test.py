import requests
import json


new_show = {
    "labolatory": "mdgt",
    "password": "it_user",

    "test_name": "triaxial",
    "object": "233445",
    "labolatory_number": 12,
    "test_type": "mdgt",

    "data": {
        "Лабораторный номер": "123-ab",
        "Модуль деформации E50, МПа": "15.8",
        "Девиатор разрушения qf, МПа": "1.02"
    }
}
response = requests.post('http://192.168.0.76:8000/report/', json=new_show)
if response.ok:
    print("Upload completed successfully!")
    with open("D:/Торренты/Курсы молчанов/Flask/qr.png", "wb") as file:
        file.write(response.content)
else:
    print("Something went wrong!")
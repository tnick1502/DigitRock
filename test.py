import os
import datetime

for entry in os.scandir("Z:/DigitRock Models Backup/112-89/Резонансная колонка"):
    if entry.is_dir():
        print(datetime.datetime.strptime(os.path.split(entry)[-1], '%d-%m-%Y %H-%M-%S'))
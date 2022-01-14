from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
import pickle

@dataclass
class ReportUnit:
    """Класс хранит одну строчку с выданными протоколами и ведомостями по объекту"""
    program: str = "unknown" # [plaxis/midas, TRM, mathCAD, dynamic, compression, triaxial]
    count: int = 0

    def __repr__(self):
        return f"[Количество: {self.count}, Программа: {self.program}]"

@dataclass
class Unit:
    """Класс хранит одну строчку с выданными протоколами и ведомостями по объекту"""
    object_number: str = None
    engineer: str = "unknown"
    report: ReportUnit = ReportUnit()
    statement: ReportUnit = ReportUnit()
    mechanics_statement: ReportUnit = ReportUnit()

    def __repr__(self):
        return f"Объект: {self.object_number}, Исполнитель: {self.engineer}, Протоколы: {self.report}, Ведомости: {self.statement}, Ведомости по механике: {self.mechanics_statement}"

class Statment:
    """Класс хранит всю ведомость выданных протоколов"""
    data: Dict[datetime, List[Unit]] = {}

    def __init__(self):
        self.data = {
            datetime(year=2019, month=1, day=1): [
                Unit(object_number="705-32", engineer="Михайлов А.И.",
                     report=ReportUnit(program="triaxial", count=5),
                     statement=ReportUnit(program="triaxial", count=5),
                     mechanics_statement=ReportUnit(program="TRM", count=5)),
                Unit(object_number="356-46", engineer="Жмылев Д.А.",
                     report=ReportUnit(program="triaxial", count=5),
                     statement=ReportUnit(program="triaxial", count=5),
                     mechanics_statement=ReportUnit(program="TRM", count=5))],
            datetime(year=2019, month=2, day=1): [
                Unit(object_number="705-32", engineer="Михайлов А.И.",
                     report=ReportUnit(program="triaxial", count=5),
                     statement=ReportUnit(program="triaxial", count=5),
                     mechanics_statement=ReportUnit(program="TRM", count=5)),
                Unit(object_number="356-46", engineer="Жмылев Д.А.",
                     report=ReportUnit(program="triaxial", count=5),
                     statement=ReportUnit(program="triaxial", count=5),
                     mechanics_statement=ReportUnit(program="TRM", count=5))]
        }

    def load_file(self, path: str):
        """Подгрузка файла ведомости"""
        self.data = Statment.read_excel_statment(path)

    def update(self):
        pass

    def dump(self, directory, name="statment.pickle"):
        with open(directory + "/" + name, "wb") as file:
            pickle.dump(self.data, file)

    def load(self, file):
        with open(file, 'rb') as f:
            self.data = pickle.load(f)

    @staticmethod
    def read_excel_statment(path: str):
        return {}

    def __repr__(self):
        return "\n".join(list(map(lambda key: f"{key.strftime('%d.%m.%Y')}: {repr(self.data[key])}", self.data)))



if __name__ == "__main__":
    x = Statment()
    print(x)


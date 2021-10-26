from excel_statment.statment_model import Statment
from excel_statment.properties_model import PhysicalProperties, MechanicalProperties, CyclicProperties, \
    DataTypeValidation, RCProperties


statment = Statment

def create_statment():
    global statment
    statment = Statment(CyclicProperties)
    statment.readExcelFile("C:/Users/Пользователь/Desktop/Тест/818-20 Атомфлот - мех.xlsx", 219)
    statment.current_test = "7а-3"

#create_statment()
# Plaxis Averaged

### Программа для усреднения кривых для верификации

#### Функционал:
* математическое усреднение кривых
* интерфейс с возможностью обработки кривых
* выдача отчетов

#### Стек:
* numpy
* scipy
* matplotlib
* reportlab
* pyqt5

#### Архитектура:
В основе 3 синглтона:
*E_models - подгружает данные с pickle
*averaged_statment (statment/avarage_model)- хранит данные усредненных кривых
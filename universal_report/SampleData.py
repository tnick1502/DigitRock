import copy

from svglib.svglib import svg2rlg

from universal_report.AttrDict import *
from reportlab.platypus.flowables import Spacer, Image
from reportlab.lib.units import inch, cm, mm
from reportlab.platypus.tables import TableStyle, Table


class UniversalInputDict:
    """
    Класс для подготовки данных для подачи в `UniversalReport`
    `UniversalReport` принимает при инициализации данные в формате настоящего класса.

    Инструкция:
    1. Запрашиваем, если необходимо, образец словаря, котороый должен быть подан в
        данный класс в set_data
    2. Заполняем параметры словаря.
        ! `lists` удобно заполнить вручную, создав с нуля и заменить образец
        ! некоторые свойства можно оформить при помощи встроенных в данный класс методов
    3. Направляем заполненный образец в `set_data` в экземпляр настоящего класса
    4. Подать на вход `UniversalReport` получившейся экземпляр класса
    """

    __input_sample = AttrDict({
        # Заглавие для всех листов
        'test_heading': 'ТЕСТОВОЕ ЗАГЛАВИЕ ДЛЯ ВСЕХ СТРАНИЦ',
        # Аккредитация в две строки
        'accreditation': [
            'АТТЕСТАТ АККРЕДИТАЦИИ №RU.MCC.АЛ.988 Срок действия с 09 января 2020г.',
            'РЕЕСТР ГЕОНАДЗОРА г. МОСКВЫ №27 (РЕЙТИНГ №4)'
        ],
        # Исполнители в оформленном виде "ключ: значение"
        'executors': {
            "Исполнители:":
                "Жмылёв Д.А., Старостин П.А., Чалая Т.А., Чипеев С.С. Михалева О.В., Горшков Е.С., Доронин С.А.",
            "Исполнительный директор / нач. ИЛ:": "Семенова О.В.",
            "Научный руководитель ИЛ:": "Академик РАЕН Озмидов О.Р. / к.т.н. Череповский А.В.",
            "Главный инженер:": "Жидков И.М."
        },
        'customer_name': 'customer_name',
        'object_name': 'object_name',
        # Список всех листов
        'lists': [{
            # ОСНОВНАЯ ТАБЛИЦА И СОПУТСТВУЮЩИЕ ДАННЫЕ
            'identificate_table': {  # Обязательно
                'code': '-',  # Обязательно
                'date': '-',  # Обязательно
                'report_number': '-',  # Обязательно
                'well': '-',  # Обязательно
                'depth': '-',  # Обязательно
                'ege': None,  # Обязательно | Может принимать None
                'lab_no': '-',  # Обязательно
                'classification': '-'  # Обязательно
            },
            # ТАБЛИЦА ФИЗИЧЕСКИЕ ХАРАКТЕРИСТИКИ
            'physical_properties_table': {  # Сам ключ обязательный, данных может не быть
                # В оформленном виде
                # 'test_prop<sup rise="2.5" size="5">3</sup>': '-2,01',
            },
            # ТАБЛИЦА СВЕДЕНИЯ ОБ ИСПЫТАНИИ
            # Содержит Словари с данными построчно. Сам ключ обязательный
            'exam_table': [
                # Если значение ключа None, то печати значения не происходит
                # {'Режим испытания': 'КД, девиаторное нагружение в кинематическом режиме'},
                # {'Оборудование': 'АСИС ГТ.2.0.5'},
                # {'Параметры образца:': None, 'Высота, мм': '71,27',
                #  'Диаметр, мм': '35,09', 'ρ, г/см<sup rise="2.5" size="5">3</sup>': '1,93'}
            ],
            # ТАБЛИЦА РЕЗУЛЬТАТОВ ИСПЫТАНИИЯ
            # Порядок в списке формирует порядок на листе, последний словарь задает таблицу с описанием
            # Для подачи рисунка или таблицы на одной строке подавать просто их
            # Для подачи пары подать список с нужным порядоком на строке
            'results_table': [  # Ключ и последелний сорварь с 'description' обязательны
                # 'sample_drawing',
                # ['sample_drawing', 'sample_drawing'],
                {
                    # 'some result data': '45,21',
                    'description': '-'  # Обязательно
                }
            ]
        }],
        'font_size': 8
    })

    def __init__(self):
        self.test_heading: 'str' = ''
        self.accred: 'list' = []
        self.participants: 'list' = []
        self.object_data: 'AttrDict' = AttrDict({})
        self.lists: 'list' = []
        self.font_size: 'int' = 8

    def set_data(self, data=None):
        if not data:
            data = AttrDict({
                # Заглавие для всех листов
                'test_heading': 'ТЕСТОВОЕ ЗАГЛАВИЕ ДЛЯ ВСЕХ СТРАНИЦ',
                # Аккредитация в две строки
                'accreditation': [
                    'АТТЕСТАТ АККРЕДИТАЦИИ №RU.MCC.АЛ.988 Срок действия с 09 января 2020г.',
                    'РЕЕСТР ГЕОНАДЗОРА г. МОСКВЫ №27 (РЕЙТИНГ №4)'
                ],
                # Исполнители в оформленном виде "ключ: значение"
                'executors': {
                    "Исполнители:":
                        "Жмылёв Д.А., Старостин П.А., Чалая Т.А., Чипеев С.С. Михалева О.В., Горшков Е.С., Доронин С.А.",
                    "Исполнительный директор / нач. ИЛ:": "Семенова О.В.",
                    "Научный руководитель ИЛ:": "Академик РАЕН Озмидов О.Р. / к.т.н. Череповский А.В.",
                    "Главный инженер:": "Жидков И.М."
                },
                'customer_name': 'customer_name',
                'object_name': 'object_name',
                # Список всех листов
                'lists': [{
                    # ОСНОВНАЯ ТАБЛИЦА И СОПУТСТВУЮЩИЕ ДАННЫЕ
                    'identificate_table': {  # Обязательно
                        'code': '1JR70-L768',  # Обязательно
                        'date': '25.11.14',  # Обязательно
                        'report_number': '48-2/555-14-1542-ШШ',  # Обязательно
                        'well': '1',  # Обязательно
                        'depth': '8,5',  # Обязательно
                        'ege': None,  # Обязательно | Может принимать None
                        'lab_no': '1-1',  # Обязательно
                        'classification': 'Глина полутвёрдая слабольдистая'  # Обязательно
                    },
                    # ТАБЛИЦА ФИЗИЧЕСКИЕ ХАРАКТЕРИСТИКИ
                    'physical_properties_table': {  # Сам ключ обязательный, данных может не быть
                        # В оформленном виде
                        'test_prop<sup rise="2.5" size="5">3</sup>': '-2,01',
                    },
                    # ТАБЛИЦА СВЕДЕНИЯ ОБ ИСПЫТАНИИ
                    # Содержит Словари с данными построчно. Сам ключ обязательный
                    'exam_table': [
                        # Если значение ключа None, то печати значения не происходит
                        {'Режим испытания': 'КД, девиаторное нагружение в кинематическом режиме'},
                        {'Оборудование': 'АСИС ГТ.2.0.5'},
                        {'Параметры образца:': None, 'Высота, мм': '71,27',
                         'Диаметр, мм': '35,09', 'ρ, г/см<sup rise="2.5" size="5">3</sup>': '1,93'}],
                    # ТАБЛИЦА РЕЗУЛЬТАТОВ ИСПЫТАНИИЯ
                    # Порядок в списке формирует порядок на листе, последний словарь задает таблицу с описанием
                    # Для подачи рисунка или таблицы на одной строке подавать просто их
                    # Для подачи пары подать список с нужным порядоком на строке
                    'results_table': [  # Ключ и последелний сорварь с 'description' обязательны
                        'sample_drawing',
                        ['sample_drawing', 'sample_drawing'],
                        {'some result data': '45,21',
                         'description': '-'  # Обязательно
                         }
                    ]
                }],
                'font_size': 8
            })

        self.test_heading = data.test_heading

        self.accred = data.accreditation

        for key in data.executors:
            self.participants.append([key, data.executors[key]])

        self.object_data = AttrDict({
            'accred': self.accred,
            'participants': self.participants,
            'customerName': data.customer_name,
            'objectName': data.object_name
        })

        for page in data.lists:
            _probe_data = page['identificate_table']
            _probe_data['physical_properties_table'] = page['physical_properties_table']

            _probe_data['results_table'] = page['results_table']

            self.lists.append(AttrDict({'probe_data': AttrDict(_probe_data),
                                        'exam_data': page['exam_table']}))

        self.font_size = data.font_size

    @property
    def get_input_sample(self):
        return self.__input_sample

    @staticmethod
    def prep_img(svg, size='full') -> 'Drawing':
        _sizes = {'full': (120, 60, 8)}
        '''размеры картинок и отступы (ширина, высота, отступ слева)'''
        _size = _sizes[size]

        drawing = svg2rlg(svg, True)
        drawing.contents[0].transform = (1, 0, 0, -1, _size[2] * mm, _size[1] * mm)
        drawing.hAlign = 'LEFT'
        drawing.vAlign = 'TOP'
        drawing.height = _size[1] * mm
        drawing.width = _size[0] * mm
        return drawing

    @staticmethod
    def prep_sigma_3(sigma_3, /) -> str:
        """
        Подготовливает под формат сигма 3 в виде списка или в виде числа
        """
        if "/" in str(sigma_3):
            __sigma_3 = str(sigma_3)
        else:
            try:
                __sigma_3 = UniversalInputDict.zap(sigma_3 / 1000, 3)
            except:
                __sigma_3 = "-"

        if isinstance(__sigma_3, list):
            __sigma_3 = UniversalInputDict.zap(sigma_3[0], 3)

        return __sigma_3

    @staticmethod
    def prep_K0(K0, /) -> str:
        """
        Подготовливает под формат сигма K0
        """
        if isinstance(K0, list):
            __K0 = UniversalInputDict.zap(K0[0], 3)
        else:
            __K0 = UniversalInputDict.zap(K0, 3)

        return __K0

    @staticmethod
    def zap(val, prec, none='-') -> str:
        """ Возвращает значение `val` в виде строки с `prec` знаков после запятой
        используя запятую как разделитель дробной части
        """
        if isinstance(val, str):
            return val
        if val is None:
            return none
        fmt = "{:." + str(int(prec)) + "f}"
        return fmt.format(val).replace(".", ",")

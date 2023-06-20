from reportlab.platypus import Table, Paragraph
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.graphics import renderPDF
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from svglib.svglib import svg2rlg
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import numpy as np

stylesheet = getSampleStyleSheet()
styles = {
        'default': ParagraphStyle(
            'default',
            fontName='Times',
            fontSize=8,
            alignment=TA_CENTER,
            valignment='MIDDLE',
        ),
'default2': ParagraphStyle(
            'default',
            fontName='Times',
            fontSize=8,
            alignment=TA_LEFT,
            valignment='MIDDLE',
        ),
'default2_min': ParagraphStyle(
            'default',
            fontName='Times',
            fontSize=5,
            alignment=TA_LEFT,
            valignment='MIDDLE',
        ),
'default3': ParagraphStyle(
            'default',
            fontName='TimesDj',
            fontSize=8,
            alignment=TA_LEFT,
            valignment='MIDDLE',
        )
}

CentralStyle = styles['default']
LeftStyle = styles['default2']
DjStyle = styles['default']
LeftStyle_min = styles['default2_min']

TextDataMainFrame = {
    "laboratory_name": {
        "ru": "МОСТДОРГЕОТРЕСТ",
        "en": "MOSTDORGEOTREST",
    },
    "name_signature": {
            "ru": "испытательная лаборатория",
            "en": "soil testing laboratory",
        },
    "address": {
        "ru": "129344, г. Москва, ул. Искры, д.31, к.1",
        "en": "129344, Moscow, Iskry street, 31, building 1",
    }
}

full_executors = True


def strNone(x):
    if x is not None:
        return str(x)
    else:
        return "-"

def str_for_excel(s):  # Проверяет строку из Exel и делает ее str. Если она пустая, то возвращает -
    if str(s) == "None":
        return '-'
    else:
        return str(s)

def zap(val, prec, none='-'):
    """ Возвращает значение `val` в виде строки с `prec` знаков после запятой
    используя запятую как разделитель дробной части
    """
    if isinstance(val, str):
        return val
    if val is None:
        return none
    fmt = "{:." + str(int(prec)) + "f}"
    return fmt.format(val).replace(".", ",")

def SaveCode(version):  # Создает защитный код и записывает его в файл
    Buk = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
               'T','U','W', 'Q', 'V', 'Z']
    Chis = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    code = str(version) + str(np.random.choice(Buk)) + str(np.random.choice(Buk)) + str(
        np.random.choice(Chis)) + str(np.random.choice(Chis)) + '-' + str(np.random.choice(Buk)) + str(
        np.random.choice(Chis)) + str(np.random.choice(Chis)) + str(np.random.choice(Chis))

    return code


def main_frame(canvas, path, Data_customer, code, list, qr_code=None):
    #if Data_customer.accreditation == "ООО":
        #accreditation = "ON"
    #elif Data_customer.accreditation == "ОАО" or Data_customer.accreditation == "АО":
        #accreditation = "AN"z

    data = Data_customer.end_date


    canvas.setLineWidth(0.3 * mm)
    canvas.rect(20 * mm, 5 * mm, 185 * mm, 287 * mm)  # Основная рамка



    # Верхняя надпись
    canvas.line((47) * mm, (280 ) * mm, (179) * mm, (280 ) * mm)  # Линия аккредитации
    canvas.drawImage(path + "Report Data/Logo2.jpg", 23 * mm, 270 * mm,
                     width=21 * mm, height=21 * mm)  # логотип

    b = svg2rlg(path + "Report Data/qr.svg")
    b.scale(0.053, 0.053)
    renderPDF.draw(b, canvas, 180 * mm, 269 * mm)

    #a = ImageReader(path + "mdgt_qr_1.png")
    #canvas.drawImage(a, 182 * mm, 270 * mm, width=20 * mm, height=20 * mm)

    canvas.setFont('TimesDj', 20)
    canvas.drawString((47) * mm, (282) * mm, "МОСТДОРГЕОТРЕСТ")
    canvas.setFont('TimesDj', 12)
    canvas.drawString((125) * mm, (284.8) * mm, "испытательная лаборатория")
    canvas.setFont('Times', 9)
    canvas.drawString((124.5) * mm, (282) * mm, "129344, г. Москва, ул. Искры, д.31, к.1")

    # Аккредитация
    A = []  # аккредитация и низ
    fi = open(path + "Report Data/Data(НЕ УДАЛЯТЬ).txt")
    line = fi.readline().strip()
    while line:
        p = line.split('\t')
        A.append(p)
        line = fi.readline().strip()
    fi.close()

    dat4 = [
        [accreditation[Data_customer.accreditation][Data_customer.accreditation_key][0]],
        [accreditation[Data_customer.accreditation][Data_customer.accreditation_key][1]],
    ]

    #if accreditation == "OS":
        #dat4 = [[A[9][1]], [A[9][2]]]
    #elif accreditation == "ON":
        #dat4 = [[A[10][1]], [A[10][2]]]
    #elif accreditation == "AS":
        #dat4 = [[A[11][1]], [A[11][2]]]
    #elif accreditation == "AN":
        #dat4 = [[A[12][1]], [A[12][2]]]
    #else:
        #dat4 = ["", ""]


    t = Table(dat4, colWidths=132 * mm, rowHeights=3 * mm)
    t.setStyle([("FONTNAME", (0, 0), (-1, -1), 'Times'),
                 ("FONTSIZE", (0, 0), (-1, -1), 7),
                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                 ("LEFTPADDING", (0, 0), (0, -1), 0),
                 ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                 ("ALIGN", (0, 0), (-1, -1), "CENTER"), ])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, (47) * mm, (273.5) * mm)



    # Исполнители
    if accreditation == "AS" or accreditation == "AN":
        s = 0
    elif accreditation == "OS" or accreditation == "ON":
        s = 5
    else:
        s = 0

    executors_data_1 = [
        ["Исполнители:", "Жмылёв Д.А., Старостин П.А., Чалая Т.А.,"],
        ["", "Михалева О.В., Горшков Е.С., Доронин С.А."],
        ["Исполнительный директор / нач. ИЛ:", "Семенова О.В."],
        ["Научный руководитель ИЛ:", "Академик РАЕН Озмидов О.Р. / к.т.н. Череповский А.В."],
        ["Главный инженер:", "Жидков И.М."]
    ]
    executors_data_2 = [
        ["Исполнитель:", "Жидков И.М."],
        ["", ""],
        ["", ""],
        ["Генеральный директор ИЛ:", "к.т.н. Череповский А.В."],
        ["", ""],
    ]

    global full_executors

    executors_data = executors_data_1 if full_executors else executors_data_2

    if qr_code:
        dat3 = [[A[0 + s][0], A[0 + s][1]],
                ['', A[0 + s][2]],
                [A[1 + s][0], A[1 + s][1]],
                [A[2 + s][0], A[2 + s][1]],
                [A[3 + s][0], A[3 + s][1]]]
        t = Table(executors_data, colWidths=68 * mm, rowHeights = 4 * mm)
        t.setStyle([("FONTNAME", (0, 0), (-1, -1), 'Times'),
                     ("FONTSIZE", (0, 0), (-1, -1), 7),
                     ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                     ("LEFTPADDING", (1, 0), (1, -1), 1.4*mm),
                    ("LEFTPADDING", (0, 0), (0, -1), 0.3 * mm),
                     ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                     ("ALIGN", (0, 0), (-1, -1), "LEFT"), ])

        t.wrapOn(canvas, 0, 0)
        t.drawOn(canvas, 25 * mm, 12 * mm)

        t = Table([["Номер документа №:", "", "", "", code, "", "", "Дата:", "",
                    str(data.strftime("%d.%m.%Y")), "", "Лист:", "", list, "", "", "", "", "", ""]], colWidths=9.775 * mm, rowHeights=5 * mm)

        canvas.line((47) * mm, (280) * mm, (179) * mm, (280) * mm)

        t.setStyle([("FONTNAME", (0, 0), (-1, -1), 'TimesK'),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("SPAN", (0, 0), (3, 0)),
                    ("SPAN", (4, 0), (6, 0)),
                    ("SPAN", (7, 0), (8, 0)),
                    ("SPAN", (9, 0), (10, 0)),
                    ("SPAN", (11, 0), (12, 0)),
                    ("SPAN", (13, 0), (14, 0)),
                    #("SPAN", (13, 0), (-1, 0)),
                    ('BOX', (0, 0), (14, -1), 0.3 * mm, "black"),
                    ('INNERGRID', (0, 0), (14, -1), 0.3 * mm, "black")])
        t.wrapOn(canvas, 0, 0)
        t.drawOn(canvas, 20 * mm, 5 * mm)

        canvas.line((158.75*1.05) * mm, (5) * mm, (158.75*1.05) * mm, (51.25*0.79) * mm)

        canvas.line((158.75*1.05) * mm, (51.25*0.79) * mm, (210-5) * mm, (51.25*0.79) * mm)

        t = Table([["Сервис georeport.ru"], [""]], colWidths=46.25*0.85*mm,
                  rowHeights=1*mm)
        t.setStyle([("FONTNAME", (0, 0), (-1, -1), 'Times'),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (1, 0), (1, -1), 1.4 * mm),
                    ("LEFTPADDING", (0, 0), (0, -1), 0.3 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"), ])
        t.wrapOn(canvas, 0, 0)
        t.drawOn(canvas, 158.75*1.05 * mm, 51.25*0.68 - 8 + 28* mm)

        # canvas.drawImage(qr_code, (8.25*0.5 + 158.75*1.05 + 0.5) * mm, (8.5*0.95) * mm,
        #                  width=(37*0.85) * mm, height=(37*0.85) * mm)
        canvas.drawImage(qr_code, (170.11875) * mm, (8.5 * 0.65) * mm,
                         width=(37 * 0.85) * mm, height=(37 * 0.85) * mm)


    else:
        dat3 = [[A[0 + s][0], A[0 + s][1]],
                ['', A[0 + s][2]],
                [A[1 + s][0], A[1 + s][1]],
                [A[2 + s][0], A[2 + s][1]],
                [A[3 + s][0], A[3 + s][1]]]
        t = Table(executors_data, colWidths=100 * mm, rowHeights=4 * mm)
        t.setStyle([("FONTNAME", (0, 0), (-1, -1), 'Times'),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (1, 0), (1, -1), 1.4 * mm),
                    ("LEFTPADDING", (0, 0), (0, -1), 0.3 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"), ])

        t.wrapOn(canvas, 0, 0)
        t.drawOn(canvas, 25 * mm, 12 * mm)

        # Нижняя таблица
        t = Table([["Номер документа №:", "", "", "", code, "", "", "", "", "", "", "Дата:", "",
                    str(data.strftime("%d.%m.%Y")), "", "", "Лист:", "", list, ""]], colWidths=9.25 * mm,
                  rowHeights=5 * mm)
        t.setStyle([("FONTNAME", (0, 0), (-1, -1), 'TimesK'),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("SPAN", (0, 0), (3, 0)),
                    ("SPAN", (4, 0), (10, 0)),
                    ("SPAN", (11, 0), (12, 0)),
                    ("SPAN", (13, 0), (15, 0)),
                    ("SPAN", (16, 0), (17, 0)),
                    ("SPAN", (18, 0), (19, 0)),
                    ('BOX', (0, 0), (-1, -1), 0.3 * mm, "black"),
                    ('INNERGRID', (0, 0), (-1, -1), 0.3 * mm, "black")])
        t.wrapOn(canvas, 0, 0)
        t.drawOn(canvas, 20 * mm, 5 * mm)

def result_table_averaged(canvas, EGE, data, y_cordinate=50):

    a = svg2rlg(data["pick"])
    a.scale(0.8, 0.8)
    renderPDF.draw(a, canvas, 25 * mm, (y_cordinate + 17) * mm)

    tableData = [[f"РЕЗУЛЬТАТЫ УСРЕДНЕНИЯ КРИВЫХ ПО ИГЭ {EGE}", "", "", "", "", ""]]
    r = 28
    for i in range(r):
        tableData.append([""])

    tableData.append(
        [Paragraph('''<p>Средний модуль деформации E<sub rise="0.5" size="6">50</sub>, МПа:</p>''', LeftStyle),
            "", "", "", zap(data["averaged_E50"], 2), ""])
    tableData.append(
        [Paragraph('''<p>Средний девиатор разрушения q<sub rise="0.5" size="6">f</sub>, МПа:</p>''', LeftStyle),
            "", "", "", zap(data["averaged_qf"], 2), ""])
    tableData.append(
        [Paragraph('''<p>Среднее эффективное сцепление с', МПа:</p>''', LeftStyle),
            "", "", "", zap(data["averaged_c"], 3), ""])
    tableData.append(
        [Paragraph('''<p>Средний эффективный угол внутреннего трения φ', град:</p>''', LeftStyle),
            "", "", "", zap(data["averaged_fi"], 1), ""])

    style = [('SPAN', (0, 0), (-1, 0)),
             ('SPAN', (0, 1), (-1, r)),

             ('SPAN', (0, -1), (3, -1)),
             ('SPAN', (-2, -1), (-1, -1)),
             ('SPAN', (0, -2), (3, -2)),
             ('SPAN', (-2, -2), (-1, -2)),
             ('SPAN', (0, -3), (3, -3)),
             ('SPAN', (-2, -3), (-1, -3)),
             ('SPAN', (0, -4), (3, -4)),
             ('SPAN', (-2, -4), (-1, -4)),

             ("BACKGROUND", (0, -1), (3, -1), HexColor(0xebebeb)),
             ("BACKGROUND", (0, -2), (3, -2), HexColor(0xebebeb)),
             ("BACKGROUND", (0, -3), (3, -3), HexColor(0xebebeb)),
             ("BACKGROUND", (0, -4), (3, -4), HexColor(0xebebeb)),

             ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
             ("FONTNAME", (0, 1), (-1, -1), 'Times'),
             ("FONTSIZE", (0, 0), (-1, -1), 8),
             # ("LEFTPADDING", (0, 1), (1, 10), 50 * mm),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("ALIGN", (0, 0), (-1, r), "CENTER"),
             ("ALIGN", (0, r + 1), (0, -1), "LEFT"),
             ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
             ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")]

    t = Table(tableData, colWidths=175 / 6 * mm, rowHeights=4 * mm)
    t.setStyle(style)

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, y_cordinate * mm)

def ege_identifier_table(canvas, data_customer, EGE, name, p_ref, K0, lname = "-СР"):  # Верхняя таблица данных

    moove = int(len(data_customer.object_name)/115) + 1
    if moove <= 3:
        moove = 3

    objectStyle = LeftStyle
    if moove >= 6:
        moove = moove -1
        objectStyle = LeftStyle_min

    t = Table([[name[0], "", "", "", "", "", "", "", "", ""],
               [name[1]],
               ["Протокол №", "", str_for_excel(EGE + "/" + data_customer.object_number + lname), "", "", "", "", "", "", ""],
               ['Заказчик:', Paragraph(data_customer.customer, LeftStyle)],
               ['Объект:', Paragraph(data_customer.object_name, objectStyle)], *[[""] for _ in range(moove)],
               ["ИГЭ/РГЭ:", "", "", Paragraph(strNone(EGE), LeftStyle)],
               [Paragraph('''<p>Референтное давление p<sub rise="2.5" size="6">ref</sub>, МПа:</p>''', LeftStyle), "", "", zap(p_ref, 3)],
               [Paragraph('''<p>K<sub rise="0.5" size="6">0</sub>, д.е.:</p>''', LeftStyle), "", "", zap(K0, 2)],
               ], colWidths=17.5 * mm, rowHeights=4 * mm)

    t.setStyle([("FONTNAME", (0, 0), (-1, 1), 'TimesDj'),
                 ("FONTNAME", (0, 2), (-1, -1), 'Times'),
                 ("FONTSIZE", (0, 0), (-1, -1), 8),
                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                 ("ALIGN", (0, 0), (-1, 1), "CENTER"),
                 ("ALIGN", (0, 2), (-1, -1), "LEFT"),
                 #("LEFTPADDING", (0, 0), (0, 0), 62 * mm),
                 #("LEFTPADDING", (1, 0), (1, 0), 3 * mm),
                 ('SPAN', (0, 0), (-1, 0)),
                 ('SPAN', (0, 1), (-1, 1)),

                 ('SPAN', (0, 2), (1, 2)), ('SPAN', (2, 2), (-1, 2)),
                 ('SPAN', (1, 3), (-1, 3)),
                 ('SPAN', (0, 4), (0, 4+moove)), ('SPAN', (1, 4), (-1, 4+moove)),
                 ('SPAN', (0, 5+moove), (2, 5+moove)), ('SPAN', (3, 5+moove), (-1, 5+moove)),
                 ('SPAN', (0, 6+moove), (2, 6+moove)), ('SPAN', (3, 6+moove), (-1, 6+moove)),
                 ('SPAN', (0, 7 + moove), (2, 7 + moove)), ('SPAN', (3, 7 + moove), (-1, 7 + moove)),
                 ("BACKGROUND", (0, 2), (1, 2), HexColor(0xebebeb)),
                 ("BACKGROUND", (0, 3), (0, 3), HexColor(0xebebeb)),
                 ("BACKGROUND", (0, 4), (0, 4), HexColor(0xebebeb)),

                 ("BACKGROUND", (0, 5+moove), (2, 5+moove), HexColor(0xebebeb)),
                 ("BACKGROUND", (0, 6+moove), (2, 6+moove), HexColor(0xebebeb)),
                 ("BACKGROUND", (0, 7+moove), (0, 7+moove), HexColor(0xebebeb)),
                 #("BACKGROUND", (0, 2), (1, 2), HexColor(0xd9d9d9)),
                 #('SPAN', (0, 2), (1, 2)),
                 ('BOX', (0, 2), (-1, -1), 0.3 * mm, "black"),
                 ('INNERGRID', (0, 2), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, (221 - (moove - 3)*4) * mm)

    return (moove-3)*4

def report_averaged(file_name, data_customer, path, data, version = 1.1, qr_code=None):  # p1 - папка сохранения отчета, p2-путь к файлу XL, Nop - номер опыта
    # Подгружаем шрифты
    pdfmetrics.registerFont(TTFont('Times', path + 'Report Data/Times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesK', path + 'Report Data/TimesK.ttf'))
    pdfmetrics.registerFont(TTFont('TimesDj', path + 'Report Data/TimesDj.ttf'))

    canvas = Canvas(file_name, pagesize=A4)
    code = SaveCode(version)
    name = [
        "УСРЕДНЕНИЕ КРИВЫХ ДЕВИАТОРНОГО НАГРУЖЕНИЯ ПО ИГЭ",
        "МЕТОДОМ АППРОКСИМАЦИИ ПОЛНОМОМ N-СТЕПЕНИ"
    ]

    page_number = 0
    pages_count = len(data)

    for EGE, report_data in data.items():
        if page_number != 0:
            canvas.showPage()
        main_frame(canvas, path, data_customer, code, f"{page_number + 1}/{pages_count}", qr_code=qr_code)
        moove = ege_identifier_table(
            canvas, data_customer, EGE, name, p_ref=data[EGE]["averaged_p_ref"] / 1000, K0=data[EGE]["averaged_K0"]
        )
        result_table_averaged(canvas, EGE, report_data, y_cordinate=80-moove)
        page_number += 1

    canvas.showPage()

    canvas.save()


if __name__ == '__main__':
    path = "C:/Users/Пользователь/PycharmProjects/DigitRock/project_data/"
    pdfmetrics.registerFont(TTFont('Times', path + 'Report Data/Times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesK', path + 'Report Data/TimesK.ttf'))
    pdfmetrics.registerFont(TTFont('TimesDj', path + 'Report Data/TimesDj.ttf'))

    canvas = Canvas("C:/Users/Пользователь/Desktop/Загрузки/test.pdf", pagesize=A4)

    code = SaveCode(1.1)
    import datetime
    customer = AttrDict({'accreditation_key': '2',
     'object_name': 'Жилой комплекс с подземной автостоянкой и сопутствующими инфраструктурными объектами по адресу: г. Москва, Ильменский проезд, вл. 4',
     'customer': 'ООО "СТФ-СТРОЙ"', 'accreditation': 'ООО', 'object_number': '762-21',
     'start_date': datetime.datetime(2021, 12, 15, 0, 0), 'end_date': datetime.datetime(2021, 12, 28, 0, 0),
     'shipment_number': '1', 'path': 'C:/Users/Пользователь/Desktop/test/762-21 Ильменский, 4 -G0.xlsx'})

    main_frame(canvas, path, customer, code, "1/1", qr_code = "C:/Users/Пользователь/PycharmProjects/DigitRock/authentication/qr.png")

    canvas.save()



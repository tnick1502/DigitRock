from reportlab.platypus import SimpleDocTemplate, BaseDocTemplate, Table, Paragraph, Frame, PageTemplate, Image
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm, cm
from reportlab.graphics import renderPDF
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from openpyxl import load_workbook
from svglib.svglib import svg2rlg  # Эта
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.utils import ImageReader

from excel_statment.params import accreditation

import ctypes
import io

def GetTextDimensions(text, points, font):
    class SIZE(ctypes.Structure):
        _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]

    hdc = ctypes.windll.user32.GetDC(0)
    hfont = ctypes.windll.gdi32.CreateFontA(points, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, font)
    hfont_old = ctypes.windll.gdi32.SelectObject(hdc, hfont)

    size = SIZE(0, 0)
    ctypes.windll.gdi32.GetTextExtentPoint32A(hdc, text, len(text), ctypes.byref(size))

    ctypes.windll.gdi32.SelectObject(hdc, hfont_old)
    ctypes.windll.gdi32.DeleteObject(hfont)

    return size.cx*0.2645833333333#(size.cx*0.2645833333333, size.cy*0.2645833333333)

from io import BytesIO

import matplotlib.pyplot as plt

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

def zap2(s, m=0):  # Количство знаков после запятой. s - число в str, m - число знаков

    if s != "-":
        if type(s) == "<class 'str'>":
            s = s.replace(",", ".")
        try:

            i = s.index(",")

            if len(s) - i > m:
                s = s[0:i + m + 1]
            elif len(s) - i <= m:
                for i in range(m - len(s) + i + 1):
                    s += "0"

        except ValueError:
            s += ","
            for i in range(m):
                s += "0"

        return s
    else:
        return s

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

def weirdo_round(val):
    if isinstance(val, str):
        return val
    if val is None:
        return None
    return int(val)+(0.5 if val-int(val) >= 0.5 else 0.0)

def SaveCode(version):  # Создает защитный код и записывает его в файл
    Buk = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
               'T','U','W', 'Q', 'V', 'Z']
    Chis = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    code = str(version) + str(np.random.choice(Buk)) + str(np.random.choice(Buk)) + str(
        np.random.choice(Chis)) + str(np.random.choice(Chis)) + '-' + str(np.random.choice(Buk)) + str(
        np.random.choice(Chis)) + str(np.random.choice(Chis)) + str(np.random.choice(Chis))

    return code



def main_frame(canvas, path, Data_customer, code, list):

    #if Data_customer.accreditation == "ООО":
        #accreditation = "ON"
    #elif Data_customer.accreditation == "ОАО" or Data_customer.accreditation == "АО":
        #accreditation = "AN"

    data = Data_customer.end_date


    canvas.setLineWidth(0.3 * mm)
    canvas.rect(20 * mm, 5 * mm, 185 * mm, 287 * mm)  # Основная рамка



    # Верхняя надпись
    canvas.line((50) * mm, (280 ) * mm, (198) * mm, (280 ) * mm)  # Линия аккредитации
    canvas.drawImage(path + "Report Data/Logo2.jpg", 23 * mm, 270 * mm,
                     width=21 * mm, height=21 * mm)  # логотип
    canvas.setFont('TimesDj', 20)
    canvas.drawString((50) * mm, (282) * mm, "МОСТДОРГЕОТРЕСТ")
    canvas.setFont('TimesDj', 12)
    canvas.drawString((130) * mm, (284.8) * mm, "испытательная лаборатория")
    canvas.setFont('Times', 10)
    canvas.drawString((130) * mm, (281) * mm, "129344, г. Москва, ул. Искры, д.31, к.1")



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


    t = Table(dat4, colWidths=145 * mm, rowHeights=3 * mm)
    t.setStyle([("FONTNAME", (0, 0), (-1, -1), 'Times'),
                 ("FONTSIZE", (0, 0), (-1, -1), 7),
                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                 ("LEFTPADDING", (0, 0), (0, -1), 0),
                 ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                 ("ALIGN", (0, 0), (-1, -1), "CENTER"), ])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, (50) * mm, (273.5) * mm)



    # Исполнители
    if accreditation == "AS" or accreditation == "AN":
        s = 0
    elif accreditation == "OS" or accreditation == "ON":
        s = 5
    else:
        s = 0

    dat3 = [[A[0 + s][0], A[0 + s][1]],
            ['', A[0 + s][2]],
            [A[1 + s][0], A[1 + s][1]],
            [A[2 + s][0], A[2 + s][1]],
            [A[3 + s][0], A[3 + s][1]]]
    t = Table(dat3, colWidths=100 * mm, rowHeights = 4 * mm)
    t.setStyle([("FONTNAME", (0, 0), (-1, -1), 'Times'),
                 ("FONTSIZE", (0, 0), (-1, -1), 8),
                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                 ("LEFTPADDING", (1, 0), (1, -1), 1.4*mm),
                ("LEFTPADDING", (0, 0), (0, -1), 0.3 * mm),
                 ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                 ("ALIGN", (0, 0), (-1, -1), "LEFT"), ])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, 12 * mm)




    # Нижняя таблица
    t = Table([["Номер документа №:", "", "", "", code, "", "", "", "", "", "", "Дата:", "", str(data.strftime("%d.%m.%Y")), "", "", "Лист:", "", list, ""]], colWidths = 9.25 * mm, rowHeights = 5 * mm)
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

def sample_identifier_table(canvas, Data_customer, Data_phiz, Lab, name, lname = "ц"):  # Верхняя таблица данных

    borehole = str(Data_phiz.borehole) if Data_phiz.borehole else "-"

    t = Table([[name[0], "", "", "", "", "", "", "", "", ""],
               [name[1]],
               ["Протокол испытаний №", "", str_for_excel(Lab + "/" + Data_customer.object_number + lname), "", "", "", "", "", "", ""],
               ['Заказчик:', Paragraph(Data_customer.customer, LeftStyle)],
               ['Объект:', Paragraph(Data_customer.object_name, LeftStyle)], [""], [""], [""],
               ["Привязка пробы (скв.; глубина отбора):", "", "", Paragraph(borehole + "; " + strNone(Data_phiz.depth).replace(".",",") +" м", LeftStyle), "", "", "ИГЭ/РГЭ:", Paragraph(strNone(Data_phiz.ige), LeftStyle)],
               ['Лабораторный номер №:', "", "", Lab],
               ['Наименование грунта:', "", Paragraph(Data_phiz.soil_name, LeftStyle)], [""]
               ], colWidths = 17.5 * mm, rowHeights = 4 * mm)



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
                 ('SPAN', (0, 4), (0, 7)), ('SPAN', (1, 4), (-1, 7)),
                 ('SPAN', (0, 8), (2, 8)), ('SPAN', (3, 8), (5, 8)), ('SPAN', (7, 8), (-1, 8)),
                 ('SPAN', (0, 9), (2, 9)), ('SPAN', (3, 9), (-1, 9)),
                 ('SPAN', (0, 10), (1, 11)), ('SPAN', (2, 10), (-1, 11)),
                 ("BACKGROUND", (0, 2), (1, 2), HexColor(0xebebeb)),
                 ("BACKGROUND", (0, 3), (0, 3), HexColor(0xebebeb)),
                 ("BACKGROUND", (0, 4), (0, 4), HexColor(0xebebeb)),

                 ("BACKGROUND", (0, 8), (2, 8), HexColor(0xebebeb)),("BACKGROUND", (6, 8), (6, 8), HexColor(0xebebeb)),
                 ("BACKGROUND", (0, 9), (2, 9), HexColor(0xebebeb)),
                 ("BACKGROUND", (0, 10), (0, 10), HexColor(0xebebeb)),
                 #("BACKGROUND", (0, 2), (1, 2), HexColor(0xd9d9d9)),
                 #('SPAN', (0, 2), (1, 2)),
                 ('BOX', (0, 2), (-1, -1), 0.3 * mm, "black"),
                 ('INNERGRID', (0, 2), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, 221 * mm)



def parameter_table(canvas, Data_phiz, Lab):  # Таблица характеристик

    data_signature = [Paragraph('''<p>ρ<sub rise="2.5" size="6">s</sub>, г/см<sup rise="2.5" size="5">3</sup></p>''', CentralStyle),
                    Paragraph('''<p>ρ, г/см<sup rise="2.5" size="5">3</sup></p>''', CentralStyle),
                    Paragraph('''<p>ρ<sub rise="2.5" size="6">d</sub>, г/см<sup rise="2.5" size="5">3</sup></p>''', CentralStyle),
                    Paragraph('''<p>n, %</p>''', CentralStyle),
                    Paragraph('''<p>e, ед.</p>''', CentralStyle),
                    Paragraph('''<p>W, %</p>''', CentralStyle),
                    Paragraph('''<p>S<sub rise="0.5" size="6">r</sub>, д.е.</p>''', CentralStyle),
                    Paragraph('''<p>I<sub rise="0.5" size="5">P</sub>, %</p>''', CentralStyle),
                    Paragraph('''<p>I<sub rise="0.5" size="5">L</sub>, ед.</p>''', CentralStyle),
                    Paragraph('''<p>I<sub rise="0.5" size="6">r</sub>, %</p>''', CentralStyle)]

    data_values = [zap(Data_phiz.rs, 2),
                 zap(Data_phiz.r, 2),
                 zap(Data_phiz.rd, 2),
                 zap(Data_phiz.n, 1),
                 zap(Data_phiz.e, 2),
                 zap(Data_phiz.W, 1),
                 zap(Data_phiz.Sr, 2),
                 zap(Data_phiz.Ip, 1),
                 zap(Data_phiz.Il, 2),
                 zap(Data_phiz.Ir, 1)]


    t = Table([["ХАРАКТЕРИСТИКИ ГРУНТА"], data_signature, data_values], colWidths=17.5 * mm, rowHeights=4 * mm)
    t.setStyle([('SPAN', (0, 0), (-1, 0)),
                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (-1, 1), HexColor(0xebebeb)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, 207 * mm)

def parameter_table_ice(canvas, wb, Nop):  # Таблица характеристик



    DataSignature = [Paragraph('''<p>T, °C</p>''', CentralStyle),
                    Paragraph('''<p>ρ<sub rise="2.5" size="6">s</sub>, г/см<sup rise="2.5" size="5">3</sup></p>''', CentralStyle),
                    Paragraph('''<p>ρ, г/см<sup rise="2.5" size="5">3</sup></p>''', CentralStyle),
                    Paragraph('''<p>ρ<sub rise="2.5" size="6">d</sub>, г/см<sup rise="2.5" size="5">3</sup></p>''', CentralStyle),
                    Paragraph('''<p>n, %</p>''', CentralStyle),
                    Paragraph('''<p>e, ед.</p>''', CentralStyle),
                    Paragraph('''<p>W<sub rise="0.5" size="6">tot</sub>, %</p>''', CentralStyle),
                    Paragraph('''<p>W<sub rise="0.5" size="6">m</sub>, %</p>''', CentralStyle),
                    Paragraph('''<p>W<sub rise="0.5" size="6">w</sub>, %</p>''', CentralStyle),
                    Paragraph('''<p>I<sub rise="0.5" size="6">tot</sub>, д.е</p>''', CentralStyle),
                    Paragraph('''<p>I<sub rise="0.5" size="6">i</sub>, д.е</p>''', CentralStyle),
                    Paragraph('''<p>S<sub rise="0.5" size="6">r</sub>, д.е.</p>''', CentralStyle),
                    Paragraph('''<p>I<sub rise="0.5" size="5">P</sub>, %</p>''', CentralStyle),
                    Paragraph('''<p>I<sub rise="0.5" size="5">L</sub>, д.е.</p>''', CentralStyle),
                    Paragraph('''<p>I<sub rise="0.5" size="6">r</sub>, %</p>''', CentralStyle),
                    Paragraph('''<p>D<sub rise="0.5" size="6">sal</sub>, %</p>''', CentralStyle)]


    DataValues = [zap(str_for_excel(wb["Лист1"]['E' + str(6 + Nop)].value).replace(".", ","), 1),
                 zap(str_for_excel(wb["Лист1"]['Q' + str(6 + Nop)].value).replace(".", ","), 2),
                 zap(str_for_excel(wb["Лист1"]['R' + str(6 + Nop)].value).replace(".", ","), 2),
                 zap(str_for_excel(wb["Лист1"]['S' + str(6 + Nop)].value).replace(".", ","), 2),
                 zap(str_for_excel(wb["Лист1"]['T' + str(6 + Nop)].value).replace(".", ","), 1),
                 zap(str_for_excel(wb["Лист1"]['U' + str(6 + Nop)].value).replace(".", ","), 2),
                 zap(str_for_excel(wb["Лист1"]['V' + str(6 + Nop)].value).replace(".", ","), 1),
                 zap(str_for_excel(wb["Лист1"]['W' + str(6 + Nop)].value).replace(".", ","), 1),
                 zap(str_for_excel(wb["Лист1"]['X' + str(6 + Nop)].value).replace(".", ","), 1),
                 zap(str_for_excel(wb["Лист1"]['Y' + str(6 + Nop)].value).replace(".", ","), 2),
                 zap(str_for_excel(wb["Лист1"]['Z' + str(6 + Nop)].value).replace(".", ","), 2),
                 zap(str_for_excel(wb["Лист1"]['AA' + str(6 + Nop)].value).replace(".", ","), 2),
                 zap(str_for_excel(wb["Лист1"]['AD' + str(6 + Nop)].value).replace(".", ","), 1),
                 zap(str_for_excel(wb["Лист1"]['AE' + str(6 + Nop)].value).replace(".", ","), 2),
                 zap(str_for_excel(wb["Лист1"]['AF' + str(6 + Nop)].value).replace(".", ","), 1),
                 zap(str_for_excel(wb["Лист1"]['AH' + str(6 + Nop)].value).replace(".", ","), 3)]


    t = Table([["ХАРАКТЕРИСТИКИ ГРУНТА"], DataSignature[0:8], DataValues[0:8], DataSignature[8:16], DataValues[8:16]], colWidths=21.875 * mm, rowHeights=4 * mm)
    t.setStyle([('SPAN', (0, 0), (-1, 0)),
                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (-1, 1), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 3), (-1, 3), HexColor(0xebebeb)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, 203 * mm)



def test_mode_rc(canvas, ro, Data):


    DataSignature = ["Режим Испытания", "Изотропная консолидация, циклическое нагружение крутящим моментом"]

    t = Table([["СВЕДЕНИЯ ОБ ИСПЫТАНИИ"],
               ["Режим испытания:", "", Data.Rezhim, "", "", "", "", "", ""],
               [Paragraph('''<p>Опорное давление p<sup rise="2.5" size="5">ref</sup>, МПа:</p>''', LeftStyle), "", zap(Data.reference_pressure, 2)],
               ["Оборудование:", "", Data.Oborudovanie],
               ["Параметры образца:", "", "Высота, мм:", zap(Data.h, 2), "Диаметр, мм:", zap(Data.d, 2), Paragraph('''<p>ρ, г/см<sup rise="2.5" size="5">3</sup>:</p>''', LeftStyle), zap(ro, 2)]], colWidths=19.444444* mm, rowHeights=4 * mm)
    t.setStyle([('SPAN', (0, 0), (-1, 0)),
                ('SPAN', (0, 1), (1, 1)),
                ('SPAN', (2, 1), (-1, 1)),
                ('SPAN', (0, 2), (1, 2)),
                ('SPAN', (2, 2), (-1, 2)),
                ('SPAN', (0, 3), (1, 3)),
                ('SPAN', (2, 3), (-1, 3)),
                ('SPAN', (0, 4), (1, 4)),
                ('SPAN', (7, 4), (8, 4)),
                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (1, 1), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 2), (1, 2), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 3), (1, 3), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 4), (1, 4), HexColor(0xebebeb)),
                ("BACKGROUND", (2, 4), (2, 4), HexColor(0xebebeb)),
                ("BACKGROUND", (4, 4), (4, 4), HexColor(0xebebeb)),
                ("BACKGROUND", (6, 4), (6, 4), HexColor(0xebebeb)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, 185 * mm)

def test_mode_triaxial_cyclic(canvas, ro, test_parameter):

    d = test_parameter["d"]
    h = test_parameter["h"]

    if test_parameter["type"] == "Сейсморазжижение" or test_parameter["type"] == "Демпфирование":

        t = Table([["СВЕДЕНИЯ ОБ ИСПЫТАНИИ"],
                   ["Режим испытания:", "", test_parameter["Rezhim"], "", "", "", "", "", ""],
                   ["Оборудование:", "", test_parameter["Oborudovanie"]],
                   ["Параметры образца:", "", "Высота, мм:", zap(str(h).replace(".", ","), 2), "Диаметр, мм:", zap(str(d).replace(".", ","), 2),
                    "", ""],
                    #Paragraph('''<p>ρ, г/см<sup rise="2.5" size="5">3</sup>:</p>''', LeftStyle), zap(str(ro).replace(".", ","), 2)],
                   [Paragraph('''<p>σ'<sub rise="2.5" size="6">3</sub>, кПа:</p>''', LeftStyle), "", zap(test_parameter["sigma3"], 0),
                    Paragraph('''<p>σ'<sub rise="2.5" size="6">1</sub>, кПа:</p>''', LeftStyle), "", zap(test_parameter["sigma1"], 0),
                    Paragraph('''<p>τ<sub rise="2.5" size="6">α</sub>, кПа:</p>''', LeftStyle), "", zap(test_parameter["tau"], 0)],
                    [Paragraph('''<p>K<sub rise="0.5" size="6">0</sub>, д.е.:</p>''', LeftStyle), "", zap(test_parameter["K0"], 2),
                    "Частота, Гц:", "", str(test_parameter["frequency"]).replace(".", ","), "I, балл:",  "", str(test_parameter["I"]).replace(".", ",") if test_parameter["I"] else "-"],
                   ["M, ед.:", "", str(test_parameter["M"]).replace(".", ",") if test_parameter["M"] else "-", "MSF, ед.:", "",str(test_parameter["MSF"]).replace(".", ",") if test_parameter["MSF"] else "-", Paragraph('''<p>r<sub rise="2.5" size="6">d</sub>, ед.:</p>''', LeftStyle), "",str(test_parameter["rd"]).replace(".", ","),]], colWidths=19.444444* mm, rowHeights=4 * mm)

    elif test_parameter["type"] == "Штормовое разжижение":
        t = Table([["СВЕДЕНИЯ ОБ ИСПЫТАНИИ"],
                   ["Режим испытания:", "", test_parameter["Rezhim"], "", "", "", "", "", ""],
                   ["Оборудование:", "", test_parameter["Oborudovanie"]],
                   ["Параметры образца:", "", "Высота, мм:", zap(str(h).replace(".", ","), 2), "Диаметр, мм:", zap(str(d).replace(".", ","), 2),
                    "", ""],
                    #Paragraph('''<p>ρ, г/см<sup rise="2.5" size="5">3</sup>:</p>''', LeftStyle),
                    #zap(str(ro).replace(".", ","), 2)],
                   [Paragraph('''<p>σ'<sub rise="2.5" size="6">3</sub>, кПа:</p>''', LeftStyle), "",
                    zap(test_parameter["sigma3"], 0),
                    Paragraph('''<p>σ'<sub rise="2.5" size="6">1</sub>, кПа:</p>''', LeftStyle), "",
                    zap(test_parameter["sigma1"], 0),
                    Paragraph('''<p>σ<sub rise="2.5" size="6">d</sub>, кПа:</p>''', LeftStyle), "",
                    zap(test_parameter["tau"]*2, 0)],
                   [Paragraph('''<p>K<sub rise="0.5" size="6">0</sub>, д.е.:</p>''', LeftStyle), "",
                    zap(test_parameter["K0"], 2),
                    "Частота, Гц:", "", str(test_parameter["frequency"]).replace(".", ","),
                    Paragraph('''<p>T<sub rise="0.5" size="6">w</sub>, с:</p>''', LeftStyle), "",
                    str(round(1/test_parameter["frequency"], 3)).replace(".", ",")],
                   [Paragraph('''<p>H<sub rise="0.5" size="6">w</sub>, м:</p>''', LeftStyle), "", zap(test_parameter["Hw"],2),
                    Paragraph('''<p>ρ<sub rise="2.5" size="6">w</sub>, кН/м<sup rise="2.5" size="5">3</sup></p>''', LeftStyle), "", zap(test_parameter["rw"], 2),
                    "", "", ""]], colWidths=19.444444 * mm, rowHeights=4 * mm)

    t.setStyle([('SPAN', (0, 0), (-1, 0)),
                ('SPAN', (0, 1), (1, 1)), ('SPAN', (2, 1), (-1, 1)),
                ('SPAN', (0, 2), (1, 2)), ('SPAN', (2, 2), (-1, 2)),
                ('SPAN', (0, 3), (1, 3)), ('SPAN', (7, 3), (8, 3)), ('SPAN', (7, 3), (8, 3)),
                ('SPAN', (0, 4), (1, 4)), ('SPAN', (3, 4), (4, 4)), ('SPAN', (6, 4), (7, 4)),
                ('SPAN', (0, 5), (1, 5)), ('SPAN', (3, 5), (4, 5)), ('SPAN', (6, 5), (7, 5)),
                ('SPAN', (0, 6), (1, 6)), ('SPAN', (3, 6), (4, 6)), ('SPAN', (6, 6), (7, 6)),
                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (1, 1), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 2), (1, 2), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 3), (1, 3), HexColor(0xebebeb)),
                ("BACKGROUND", (2, 3), (2, 3), HexColor(0xebebeb)),
                ("BACKGROUND", (4, 3), (4, 3), HexColor(0xebebeb)),
                ("BACKGROUND", (6, 3), (6, 3), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 4), (1, 6), HexColor(0xebebeb)),
                ("BACKGROUND", (3, 4), (4, 6), HexColor(0xebebeb)),
                ("BACKGROUND", (6, 4), (7, 6), HexColor(0xebebeb)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, 177 * mm)

def test_mode_vibration_creep(canvas, test_parameter):

    d = test_parameter["d"]
    h = test_parameter["h"]

    frequency = ""
    for i in range(len(test_parameter["frequency"])):
        frequency += zap(test_parameter["frequency"][i], 1) + "; "

    t = Table([["СВЕДЕНИЯ ОБ ИСПЫТАНИИ"],
               ["Режим испытания:", "", test_parameter["Rezhim"], "", "", "", "", "", ""],
               ["Оборудование:", "", test_parameter["Oborudovanie"]],
               ["Параметры образца:", "", "Высота, мм:", zap(str(h).replace(".", ","), 2), "Диаметр, мм:", zap(str(d).replace(".", ","), 2),
                Paragraph('''<p>Частота, Гц</p>''', LeftStyle), frequency],
                #Paragraph('''<p>ρ, г/см<sup rise="2.5" size="5">3</sup>:</p>''', LeftStyle), zap(str(ro).replace(".", ","), 2)],
               [Paragraph('''<p>σ'<sub rise="2.5" size="6">3</sub>, кПа:</p>''', LeftStyle), "", zap(test_parameter["sigma_3"], 0),
                "", "", "",
                Paragraph('''<p>τ<sub rise="2.5" size="6">α</sub>, кПа:</p>''', LeftStyle), "", zap(test_parameter["t"], 0)]],
              colWidths=19.444444* mm, rowHeights=4 * mm)

    t.setStyle([('SPAN', (0, 0), (-1, 0)),
                ('SPAN', (0, 1), (1, 1)), ('SPAN', (2, 1), (-1, 1)),
                ('SPAN', (0, 2), (1, 2)), ('SPAN', (2, 2), (-1, 2)),
                ('SPAN', (0, 3), (1, 3)), ('SPAN', (7, 3), (8, 3)), ('SPAN', (7, 3), (8, 3)),
                ('SPAN', (0, 4), (1, 4)), ('SPAN', (3, 4), (4, 4)), ('SPAN', (6, 4), (7, 4)),
                ('SPAN', (0, 5), (1, 5)), ('SPAN', (3, 5), (4, 5)), ('SPAN', (6, 5), (7, 5)),
                ('SPAN', (0, 6), (1, 6)), ('SPAN', (3, 6), (4, 6)), ('SPAN', (6, 6), (7, 6)),
                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (1, 1), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 2), (1, 2), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 3), (1, 3), HexColor(0xebebeb)),
                ("BACKGROUND", (2, 3), (2, 3), HexColor(0xebebeb)),
                ("BACKGROUND", (4, 3), (4, 3), HexColor(0xebebeb)),
                ("BACKGROUND", (6, 3), (6, 3), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 4), (1, 6), HexColor(0xebebeb)),
                ("BACKGROUND", (3, 4), (4, 6), HexColor(0xebebeb)),
                ("BACKGROUND", (6, 4), (7, 6), HexColor(0xebebeb)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, 185 * mm)

def test_mode_consolidation(canvas, Data):

    if "/" in str(Data["sigma_3"]):
        sigma_3 = str(Data["sigma_3"])
    else:
        try:
            sigma_3 = zap(Data["sigma_3"] / 1000, 3)
        except:
            sigma_3 = "-"

    t = Table([["СВЕДЕНИЯ ОБ ИСПЫТАНИИ"],
               ["Режим испытания:", "", "", Data["mode"], "", "", "", "", "", ""],
               [Paragraph('''<p>Боковое давление σ<sub rise="2.5" size="6">3</sub>, МПа:</p>''', LeftStyle), "", "", sigma_3, "", Paragraph('''<p>K<sub rise="2.5" size="6">0</sub>, д.е.:</p>''', LeftStyle), "", "", zap(Data["K0"], 2), ""],
               ["Оборудование:", "", "", "ЛИГА КЛ-1С, АСИС ГТ.2.0.5, GIESA UP-25a"],
               ["Параметры образца:", "", "", "Высота, мм:", "", zap(Data["h"], 2), "Диаметр, мм:", "", zap(Data["d"], 2), ""]], colWidths=17.5* mm, rowHeights=4 * mm)
    t.setStyle([('SPAN', (0, 0), (-1, 0)),
                ('SPAN', (0, 1), (2, 1)),
                ('SPAN', (3, 1), (-1, 1)),
                ('SPAN', (0, 2), (2, 2)),
                ('SPAN', (3, 2), (4, 2)),
                ('SPAN', (5, 2), (7, 2)),
                ('SPAN', (8, 2), (9, 2)),
                ('SPAN', (0, 3), (2, 3)),
                ('SPAN', (3, 3), (-1, 3)),
                ('SPAN', (0, 4), (2, 4)),
                ('SPAN', (3, 4), (4, 4)),
                ('SPAN', (6, 4), (7, 4)),
                ('SPAN', (8, 4), (9, 4)),
                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (2, 1), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 2), (2, 2), HexColor(0xebebeb)),
                ("BACKGROUND", (5, 2), (7, 2), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 3), (2, 3), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 4), (4, 4), HexColor(0xebebeb)),
                ("BACKGROUND", (6, 4), (7, 4), HexColor(0xebebeb)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, 185 * mm)

def test_mode_consolidation_1(canvas, Data):


    t = Table([["СВЕДЕНИЯ ОБ ИСПЫТАНИИ"],
               ["Режим испытания:", "", "", Data["mode"], "", "", "", "", "", ""],
               [Paragraph('''<p>Давление консолидации σ, МПа:</p>''', LeftStyle), "", "", Data["p_max"], "", "", "", "", "", ""],
               ["Оборудование:", "", "", Data["equipment"]],
               ["Параметры образца:", "", "", "Высота, мм:", "", zap(Data["h"], 2), "Диаметр, мм:", "", zap(Data["d"], 2), ""]], colWidths=17.5* mm, rowHeights=4 * mm)
    t.setStyle([('SPAN', (0, 0), (-1, 0)),
                ('SPAN', (0, 1), (2, 1)),
                ('SPAN', (3, 1), (-1, 1)),
                ('SPAN', (0, 2), (2, 2)),
                ('SPAN', (3, 2), (9, 2)),
                ('SPAN', (0, 3), (2, 3)),
                ('SPAN', (3, 3), (-1, 3)),
                ('SPAN', (0, 4), (2, 4)),
                ('SPAN', (3, 4), (4, 4)),
                ('SPAN', (6, 4), (7, 4)),
                ('SPAN', (8, 4), (9, 4)),
                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (2, 1), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 2), (2, 2), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 3), (2, 3), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 4), (4, 4), HexColor(0xebebeb)),
                ("BACKGROUND", (6, 4), (7, 4), HexColor(0xebebeb)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, 185 * mm)

def testModeStamm(canvas, wb, Nop, Data):

    d = np.random.uniform(-0.15, 0.15) + Data["d"]
    h = np.random.uniform(-0.15, 0.15) + Data["h"]
    try:
        ro = np.random.uniform(-0.02, 0.02) + float(str_for_excel(wb["Лист1"]['R' + str(6 + Nop)].value))
    except ValueError:
        ro = "-"

    t = Table([["СВЕДЕНИЯ ОБ ИСПЫТАНИИ"],
               ["Режим испытания:", "", Data["Rezhim"], "", "", "", "", "", ""],
               ["Температура испытания, °C:", "", zap(str_for_excel(wb["Лист1"]['E' + str(6 + Nop)].value).replace(".", ","), 1)],
               ["Оборудование:", "", Data["Oborudovanie"]],
               ["Параметры образца:", "", "Высота, мм:", zap(str(h).replace(".", ","), 2), "Диаметр, мм:", zap(str(d).replace(".", ","),2), Paragraph('''<p>ρ, г/см<sup rise="2.5" size="5">3</sup>:</p>''', LeftStyle), zap(str(ro).replace(".", ","),2)]], colWidths=19.444444* mm, rowHeights=4 * mm)
    t.setStyle([('SPAN', (0, 0), (-1, 0)),
                ('SPAN', (0, 1), (1, 1)),
                ('SPAN', (2, 1), (-1, 1)),
                ('SPAN', (0, 2), (1, 2)),
                ('SPAN', (2, 2), (-1, 2)),
                ('SPAN', (0, 3), (1, 3)),
                ('SPAN', (2, 3), (-1, 3)),
                ('SPAN', (0, 4), (1, 4)),
                ('SPAN', (7, 4), (8, 4)),
                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (1, 1), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 2), (1, 2), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 3), (1, 3), HexColor(0xebebeb)),
                ("BACKGROUND", (0, 4), (1, 4), HexColor(0xebebeb)),
                ("BACKGROUND", (2, 4), (2, 4), HexColor(0xebebeb)),
                ("BACKGROUND", (4, 4), (4, 4), HexColor(0xebebeb)),
                ("BACKGROUND", (6, 4), (6, 4), HexColor(0xebebeb)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, 181 * mm)



def result_table_rc(canvas, Res, pick, scale = 0.8):


    #a = Image(pick, 320, 240)
    a = svg2rlg(pick)
    a.scale(scale, scale)
    renderPDF.draw(a, canvas, 38 * mm, 95 * mm)
    #renderPDF.draw(a, canvas, 112.5 * mm, 110 * mm)

    tableData = [["РЕЗУЛЬТАТЫ ИСПЫТАНИЯ", ""]]
    r = 25
    for i in range(r):
        tableData.append([""])

    tableData.append([Paragraph('''<p>Модуль сдвига при сверхмалых деформациях G<sub rise="0.5" size="5">0</sub>, МПа:</p>''', LeftStyle), zap(Res["G0"], 1)])
    tableData.append([Paragraph('''<p>Пороговое значение сдвиговой деформации γ<sub rise="0.5" size="5">0.7</sub>, д.е.:</p>''', LeftStyle), Paragraph('<p>' + zap(Res["gam07"], 2) + '*10<sup rise="2.5" size="5">-4</sup><p>', CentralStyle)])
    t = Table(tableData, colWidths=87.5 * mm, rowHeights=4 * mm)
    t.setStyle([('SPAN', (0, 0), (-1, 0)),
                ('SPAN', (0, 1), (1, r)),
                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                #("LEFTPADDING", (0, 1), (1, 10), 50 * mm),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, 11), "CENTER"),
                ("ALIGN", (0, 12), (0, -1), "LEFT"),
                ("ALIGN", (1, 12), (1, -1), "CENTER"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, (51-(( r-30)*4)) * mm)

def result_table__triaxial_cyclic(canvas, Res, pick, scale = 0.8):


    #a = Image(pick, 320, 240)
    if len(pick)>1:
        try:
            a = svg2rlg(pick[0])
            a.scale(scale, scale)
            renderPDF.draw(a, canvas, 36 * mm, 81 * mm)
            b = svg2rlg(pick[1])
            b.scale(scale, scale)
            renderPDF.draw(b, canvas, 120 * mm, 81 * mm)
        except AttributeError:
            a = ImageReader(pick[0])
            canvas.drawImage(a, 31 * mm, 81 * mm,
                             width=80* mm, height=80 * mm)
            b = ImageReader(pick[1])
            canvas.drawImage(b, 115 * mm, 81 * mm,
                             width=80 * mm, height=80 * mm)

    else:
        try:
            a = svg2rlg(pick[0])
            a.scale(scale, scale)
            renderPDF.draw(a, canvas, 36 * mm, 81 * mm)
        except AttributeError:
            a = ImageReader(pick[0])
            canvas.drawImage(a, 36 * mm, 81 * mm,
                             width=150 * mm, height=85 * mm)


    #renderPDF.draw(a, canvas, 112.5 * mm, 110 * mm)

    tableData = [["РЕЗУЛЬТАТЫ ИСПЫТАНИЯ", "", "", "", "", ""]]
    r = 25
    for i in range(r):
        tableData.append([""])

    tableData.append([Paragraph('''<p>PPR<sub rise="0.5" size="6">max</sub>, д.е.:</p>''', LeftStyle), zap(Res["PPRmax"], 3), Paragraph('''<p>ε<sub rise="0.5" size="6">max</sub>, д.е.:</p>''', LeftStyle), zap(Res["EPSmax"],3), Paragraph('''<p>N<sub rise="0.5" size="6">fail</sub>, ед.:</p>''', LeftStyle), zap(Res["nc"],0)])
    tableData.append(["Итог испытания:", Res["res"], "", "", "", ""])
    t = Table(tableData, colWidths=175/6 * mm, rowHeights = 4 * mm)
    t.setStyle([('SPAN', (0, 0), (-1, 0)),
                ('SPAN', (0, 1), (-1, r)),
                ('SPAN', (1, -1), (-1, -1)),
                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (2, -2), (2, -2), HexColor(0xebebeb)),
                ("BACKGROUND", (4, -2), (4, -2), HexColor(0xebebeb)),
                ("BACKGROUND", (0, -2), (0, -2), HexColor(0xebebeb)),
                ("BACKGROUND", (0, -1), (0, -1), HexColor(0xebebeb)),
                #("LEFTPADDING", (0, 1), (1, 10), 50 * mm),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, r), "CENTER"),
                ("ALIGN", (0, r+1), (0, -1), "LEFT"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, (42-(( r-30)*4)) * mm)

def result_table_consolidation(canvas, Res, pick, scale = 0.8):

    try:
        a = svg2rlg(pick[0])
        a.scale(scale, scale)
        renderPDF.draw(a, canvas, 36 * mm, 81 * mm)
        b = svg2rlg(pick[1])
        b.scale(scale, scale)
        renderPDF.draw(b, canvas, 120 * mm, 81 * mm)
    except AttributeError:
        a = ImageReader(pick[0])
        canvas.drawImage(a, 31 * mm, 81 * mm,
                             width=80* mm, height=80 * mm)
        b = ImageReader(pick[1])
        canvas.drawImage(b, 115 * mm, 81 * mm,
                             width=80 * mm, height=80 * mm)

    #renderPDF.draw(a, canvas, 112.5 * mm, 110 * mm)

    tableData = [["РЕЗУЛЬТАТЫ ИСПЫТАНИЯ", "", "", "", "", ""]]
    r = 25
    for i in range(r):
        tableData.append([""])

    tableData.append(["Метод обработки данных", "", "", "", Paragraph('''<p>√<span>t</span></p>''', LeftStyle), "ln(t)"])
    tableData.append([Paragraph('''<p>Коэффициент фильтрационной консолидации C<sub rise="0.5" size="6">v</sub>, м/сут<sup rise="2.5" size="5">2</sup>:</p>''', LeftStyle), "", "", "", Res["Cv_sqrt"], Res["Cv_log"]])
    tableData.append([Paragraph('''<p>Коэффициент вторичной консолидации C<sub rise="0.5" size="6">а</sub>:</p>''', LeftStyle), "", "", "", Res["Ca_sqrt"], Res["Ca_log"]])
    t = Table(tableData, colWidths=175/6 * mm, rowHeights = 4 * mm)
    t.setStyle([('SPAN', (0, 0), (-1, 0)),
                ('SPAN', (0, 1), (-1, r)),

                ('SPAN', (0, -1), (3, -1)),
                #('SPAN', (2, -1), (3, -1)),
                #('SPAN', (4, -1), (5, -1)),
                ('SPAN', (0, -2), (3, -2)),
                #('SPAN', (2, -2), (3, -2)),
                #('SPAN', (4, -2), (5, -2)),
                ('SPAN', (0, -3), (3, -3)),
                #('SPAN', (2, -3), (3, -3)),
              #  ('SPAN', (4, -3), (5, -3)),

                ("BACKGROUND", (0, -1), (3, -1), HexColor(0xebebeb)),
                ("BACKGROUND", (0, -2), (3, -2), HexColor(0xebebeb)),
                ("BACKGROUND", (0, -3), (3, -3), HexColor(0xebebeb)),

                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                #("LEFTPADDING", (0, 1), (1, 10), 50 * mm),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, r), "CENTER"),
                ("ALIGN", (0, r+1), (0, -1), "LEFT"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, (42-(( r-30)*4)) * mm)

def result_table_deviator(canvas, Res, pick, scale = 0.8):

    tableData = [["РЕЗУЛЬТАТЫ ИСПЫТАНИЯ", "", "", "", "", ""]]
    r = 30

    def str_Kf(x):
        s = "{:.2e}".format(x).replace(".", ",")
        return s[:-4], str(int(s[5:]))

    kf, pow = str_Kf(Res["Kf_log"])

    for i in range(r):
        tableData.append([""])

    tableData.append(
        [Paragraph('''<p>Коэффициент фильтрационной консолидации C<sub rise="0.5" size="6">v</sub>, см<sup rise="2" size="6">2</sup>/мин:</p>''', LeftStyle), "", "", "",
         zap(Res["Cv_log"], 4), ""])
    tableData.append(
        [Paragraph('''<p>Коэфффициент вторичной консолидации C<sub rise="0.5" size="6">a</sub>:</p>''', LeftStyle), "", "", "",
         zap(Res["Ca_log"], 4), ""])
    tableData.append([Paragraph('''<p>Коэффициент фильтрации, м/сут:</p>''', LeftStyle), "", "", "",
                      Paragraph(f'''<p>{kf}*10<sup rise="2" size="6">{pow}</sup></p>''', LeftStyle), ""])


    try:
        a = svg2rlg(pick[0])
        a.scale(scale, scale)
        renderPDF.draw(a, canvas, 36 * mm, 118 * mm)
        b = svg2rlg(pick[1])
        b.scale(scale, scale)
        renderPDF.draw(b, canvas, 36 * mm, 62 * mm)
    except AttributeError:
        a = ImageReader(pick[1])
        canvas.drawImage(a, 32 * mm, 60 * mm,
                         width=160 * mm, height=54 * mm)
        b = ImageReader(pick[0])
        canvas.drawImage(b, 32 * mm, 114 * mm,
                         width=160 * mm, height=54 * mm)

    style = [('SPAN', (0, 0), (-1, 0)),
             ('SPAN', (0, 1), (-1, r)),

             ('SPAN', (0, -1), (3, -1)),
             ('SPAN', (-2, -1), (-1, -1)),
             # ('SPAN', (2, -1), (3, -1)),
             # ('SPAN', (4, -1), (5, -1)),
             ('SPAN', (0, -2), (3, -2)),
             ('SPAN', (-2, -2), (-1, -2)),
             # ('SPAN', (2, -2), (3, -2)),
             # ('SPAN', (4, -2), (5, -2)),
             ('SPAN', (0, -3), (3, -3)),
             ('SPAN', (-2, -3), (-1, -3)),


             ("BACKGROUND", (0, -1), (3, -1), HexColor(0xebebeb)),
             ("BACKGROUND", (0, -2), (3, -2), HexColor(0xebebeb)),
             ("BACKGROUND", (0, -3), (3, -3), HexColor(0xebebeb)),

             ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
             ("FONTNAME", (0, 1), (-1, -1), 'Times'),
             ("FONTSIZE", (0, 0), (-1, -1), 8),
             # ("LEFTPADDING", (0, 1), (1, 10), 50 * mm),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("ALIGN", (0, 0), (-1, r), "CENTER"),
             ("ALIGN", (0, r + 1), (0, -1), "LEFT"),
             ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
             ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")]

    t = Table(tableData, colWidths=175/6 * mm, rowHeights = 4 * mm)
    t.setStyle(style)

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, (48-((r-30)*4) - 4) * mm)

def result_table_deviator1(canvas, Res, pick, scale = 0.8):

    tableData = [["РЕЗУЛЬТАТЫ ИСПЫТАНИЯ", "", "", "", "", ""]]
    r = 28
    for i in range(r):
        tableData.append([""])

    if Res["Eur"]:
        a = svg2rlg(pick[0])
        a.scale(scale, scale)
        renderPDF.draw(a, canvas, 36 * mm, 66 * mm)
        tableData.append(
            [Paragraph('''<p>Девиатор разрушения q<sub rise="0.5" size="6">f</sub>, МПа:</p>''', LeftStyle), "", "", "",
             Res["qf"], ""])
        tableData.append(
            [Paragraph('''<p>Модуль деформации E<sub rise="0.5" size="6">50</sub>, МПа:</p>''', LeftStyle), "", "", "",
             Res["E50"], ""])
        tableData.append(
            [Paragraph('''<p>Коэффициент поперечного расширения ν, д.е.:</p>''', LeftStyle), "", "", "", Res["poissons_ratio"], ""])
        tableData.append(
            [Paragraph('''<p>Разгрузочный модуль E<sub rise="0.5" size="6">ur</sub>, МПа:</p>''', LeftStyle), "", "",
             "", Res["Eur"], ""])

    else:
        E = Res["E"][0] if Res["E"][0] > Res["E50"] else "-"
        tableData.append(
            [Paragraph('''<p>Девиатор разрушения q<sub rise="0.5" size="6">f</sub>, МПа:</p>''', LeftStyle), "", "", "",
             Res["qf"], ""])
        tableData.append(
            [Paragraph('''<p>Модуль деформации E<sub rise="0.5" size="6">50</sub>, МПа:</p>''', LeftStyle), "", "", "",
             Res["E50"], ""])
        tableData.append([Paragraph('''<p>Модуль деформации E, МПа:</p>''', LeftStyle), "", "", "", E, ""])
        tableData.append(
            [Paragraph('''<p>Коэффициент поперечной деформации ν, д.е.:</p>''', LeftStyle), "", "", "", Res["poissons_ratio"], ""])

        try:
            a = svg2rlg(pick[0])
            a.scale(scale, scale)
            renderPDF.draw(a, canvas, 36 * mm, 120 * mm)
            b = svg2rlg(pick[1])
            b.scale(scale, scale)
            renderPDF.draw(b, canvas, 36 * mm, 66 * mm)
        except AttributeError:
            a = ImageReader(pick[1])
            canvas.drawImage(a, 32 * mm, 60 * mm,
                             width=160 * mm, height=54 * mm)
            b = ImageReader(pick[0])
            canvas.drawImage(b, 32 * mm, 114 * mm,
                             width=160 * mm, height=54 * mm)

    style = [('SPAN', (0, 0), (-1, 0)),
             ('SPAN', (0, 1), (-1, r)),

             ('SPAN', (0, -1), (3, -1)),
             ('SPAN', (-2, -1), (-1, -1)),
             # ('SPAN', (2, -1), (3, -1)),
             # ('SPAN', (4, -1), (5, -1)),
             ('SPAN', (0, -2), (3, -2)),
             ('SPAN', (-2, -2), (-1, -2)),
             # ('SPAN', (2, -2), (3, -2)),
             # ('SPAN', (4, -2), (5, -2)),
             ('SPAN', (0, -3), (3, -3)),
             ('SPAN', (-2, -3), (-1, -3)),

             ('SPAN', (0, -4), (3, -4)),
             ('SPAN', (-2, -4), (-1, -4)),
             # ('SPAN', (2, -3), (3, -3)),
             #  ('SPAN', (4, -3), (5, -3)),

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

    t = Table(tableData, colWidths=175/6 * mm, rowHeights = 4 * mm)
    t.setStyle(style)

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, (42-((r-30)*4) - 4) * mm)

def result_table_deviator_vc(canvas, Res, pick, scale = 0.8):

    tableData = [["РЕЗУЛЬТАТЫ ИСПЫТАНИЯ", "", "", "", "", ""]]
    r = 29
    for i in range(r):
        tableData.append([""])

    tableData.append(
        [Paragraph('''<p>Девиатор разрушения q<sub rise="0.5" size="6">f</sub>, МПа:</p>''', LeftStyle), "", "", "",
         Res["qf"], ""])
    tableData.append([Paragraph('''<p>Модуль деформации E, МПа:</p>''', LeftStyle), "", "", "", Res["E"][0], ""])
    tableData.append(
        [Paragraph('''<p>Коэффициент поперечной деформации ν, д.е.:</p>''', LeftStyle), "", "", "", Res["poissons_ratio"], ""])

    a = ImageReader(pick[1])
    canvas.drawImage(a, 32 * mm, 60 * mm,
                     width=160 * mm, height=54 * mm)
    b = ImageReader(pick[0])
    canvas.drawImage(b, 32 * mm, 114 * mm,
                     width=160 * mm, height=54 * mm)


    style = [('SPAN', (0, 0), (-1, 0)),
             ('SPAN', (0, 1), (-1, r)),

             ('SPAN', (0, -1), (3, -1)),
             ('SPAN', (-2, -1), (-1, -1)),
             # ('SPAN', (2, -1), (3, -1)),
             # ('SPAN', (4, -1), (5, -1)),
             ('SPAN', (0, -2), (3, -2)),
             ('SPAN', (-2, -2), (-1, -2)),
             # ('SPAN', (2, -2), (3, -2)),
             # ('SPAN', (4, -2), (5, -2)),
             ('SPAN', (0, -3), (3, -3)),
             ('SPAN', (-2, -3), (-1, -3)),

             # ('SPAN', (2, -3), (3, -3)),
             #  ('SPAN', (4, -3), (5, -3)),

             ("BACKGROUND", (0, -1), (3, -1), HexColor(0xebebeb)),
             ("BACKGROUND", (0, -2), (3, -2), HexColor(0xebebeb)),
             ("BACKGROUND", (0, -3), (3, -3), HexColor(0xebebeb)),
             ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
             ("FONTNAME", (0, 1), (-1, -1), 'Times'),
             ("FONTSIZE", (0, 0), (-1, -1), 8),
             # ("LEFTPADDING", (0, 1), (1, 10), 50 * mm),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("ALIGN", (0, 0), (-1, r), "CENTER"),
             ("ALIGN", (0, r + 1), (0, -1), "LEFT"),
             ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
             ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")]

    t = Table(tableData, colWidths=175/6 * mm, rowHeights = 4 * mm)
    t.setStyle(style)

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, (42-((r-30)*4) - 4) * mm)



def result_table_deviator_reload(canvas, Res, pick, scale = 0.8):

    try:
        a = svg2rlg(pick[0])
        a.scale(scale, scale)
        renderPDF.draw(a, canvas, 36 * mm, 120 * mm)
        b = svg2rlg(pick[1])
        b.scale(scale, scale)
        renderPDF.draw(b, canvas, 36 * mm, 66 * mm)
    except AttributeError:
        a = ImageReader(pick[1])
        canvas.drawImage(a, 32 * mm, 60 * mm,
                         width=160 * mm, height=54 * mm)
        b = ImageReader(pick[0])
        canvas.drawImage(b, 32 * mm, 114 * mm,
                         width=160 * mm, height=54 * mm)

    #renderPDF.draw(a, canvas, 112.5 * mm, 110 * mm)

    tableData = [["РЕЗУЛЬТАТЫ ИСПЫТАНИЯ", "", "", "", "", ""]]
    r = 28
    for i in range(r):
        tableData.append([""])

    tableData.append([Paragraph('''<p>Девиатор разрушения q<sub rise="0.5" size="6">f</sub>, МПа:</p>''', LeftStyle), "", "", "", Res["qf"], ""])
    tableData.append([Paragraph('''<p>Модуль деформации E<sub rise="0.5" size="6">50</sub>, МПа:</p>''', LeftStyle), "", "", "", Res["E50"], ""])
    tableData.append([Paragraph('''<p>Коэффициент пуассона µ, д.е.:</p>''', LeftStyle), "", "", "", Res["poissons_ratio"], ""])
    if Res["Eur"]:
        tableData.append([Paragraph('''<p>Разгрузочный модуль E<sub rise="0.5" size="6">ur</sub>, МПа:</p>''', LeftStyle), "", "", "", Res["Eur"], ""])
    t = Table(tableData, colWidths=175/6 * mm, rowHeights=4 * mm)
    t.setStyle([('SPAN', (0, 0), (-1, 0)),
                ('SPAN', (0, 1), (-1, r)),

                ('SPAN', (0, -1), (3, -1)),
                ('SPAN', (-2, -1), (-1, -1)),
                #('SPAN', (2, -1), (3, -1)),
                #('SPAN', (4, -1), (5, -1)),
                ('SPAN', (0, -2), (3, -2)),
                ('SPAN', (-2, -2), (-1, -2)),
                #('SPAN', (2, -2), (3, -2)),
                #('SPAN', (4, -2), (5, -2)),
                ('SPAN', (0, -3), (3, -3)),
                ('SPAN', (-2, -3), (-1, -3)),
                #('SPAN', (2, -3), (3, -3)),
              #  ('SPAN', (4, -3), (5, -3)),

                ("BACKGROUND", (0, -1), (3, -1), HexColor(0xebebeb)),
                ("BACKGROUND", (0, -2), (3, -2), HexColor(0xebebeb)),
                ("BACKGROUND", (0, -3), (3, -3), HexColor(0xebebeb)),

                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                #("LEFTPADDING", (0, 1), (1, 10), 50 * mm),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, r), "CENTER"),
                ("ALIGN", (0, r+1), (0, -1), "LEFT"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, (42-(( r-30)*4)) * mm)

def result_table_cyclic_damping(canvas, Res, pick, scale = 0.8):
    try:
        a = svg2rlg(pick[0])
        a.scale(scale, scale)
        renderPDF.draw(a, canvas, 50 * mm, 45 * mm)
    except AttributeError:
        a = ImageReader(pick[0])
        canvas.drawImage(a, 55 * mm, 55 * mm,
                         width=110 * mm, height=110 * mm)


    #renderPDF.draw(a, canvas, 112.5 * mm, 110 * mm)

    tableData = [["РЕЗУЛЬТАТЫ ИСПЫТАНИЯ", "", "", "", "", ""]]
    r = 29
    for i in range(r):
        tableData.append([""])

    tableData.append([Paragraph('''<p>Коэффициент демпфирования, %:</p>''', LeftStyle), "", "",
                      zap(Res["damping_ratio"], 2), "", ""])
    tableData.append([Paragraph('''<p>Модуль упругости E, МПа:</p>''', LeftStyle), "", "",
                      zap(Res["damping_ratio"], 2), "", ""])

    t = Table(tableData, colWidths=175/6 * mm, rowHeights = 4 * mm)
    t.setStyle([('SPAN', (0, 0), (-1, 0)),
                ('SPAN', (0, 1), (-1, r)),
                ('SPAN', (0, -2), (2, -2)),
                ('SPAN', (3, -2), (5, -2)),
                ('SPAN', (0, -1), (2, -1)),
                ('SPAN', (3, -1), (5, -1)),
                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (2, -2), (2, -2), HexColor(0xebebeb)),
                ("BACKGROUND", (0, -2), (2, -2), HexColor(0xebebeb)),
                ("BACKGROUND", (0, -1), (2, -1), HexColor(0xebebeb)),
                #("LEFTPADDING", (0, 1), (1, 10), 50 * mm),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, r), "CENTER"),
                ("ALIGN", (0, r+1), (0, -1), "LEFT"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, 45 * mm)



def result_vibration_creep(canvas, Res, pick, scale = 0.8):

    try:
        a = ImageReader(pick[1])
        canvas.drawImage(a, 32 * mm, 60 * mm,
                         width=160 * mm, height=54 * mm)
        b = ImageReader(pick[0])
        canvas.drawImage(b, 32 * mm, 114 * mm,
                         width=160 * mm, height=54 * mm)

    except AttributeError:
        print("lksdfksdfkmsdf")

    #renderPDF.draw(a, canvas, 112.5 * mm, 110 * mm)

    tableData = [["РЕЗУЛЬТАТЫ ИСПЫТАНИЯ", "", "", "", "", ""]]
    r = 28
    for i in range(r):
        tableData.append([""])

    if len(Res) > 1:
        Kd = ""
        Ed = ""
        E50 = ""
        prediction = ""
        for i in range(len(Res)):
            Kd += zap(Res[i]["Kd"], 2) + "; "
            Ed += zap(Res[i]["E50d"], 2) + "; "
            E50 += zap(Res[i]["E50"], 2) + "; "
            prediction += zap(Res[i]["prediction"]["50_years"], 3) + "; "
    else:
        Kd = zap(Res[0]["Kd"], 2)
        Ed = zap(Res[0]["E50d"], 2)
        E50 = zap(Res[0]["E50"], 2)
        prediction = zap(Res[0]["prediction"]["50_years"], 3)

    tableData.append(
        [Paragraph(
            '''<p>Модуль деформации E<sub rise="0.5" size="6">50</sub>, МПа:</p>''',
            LeftStyle), "",
         "", "", E50, ""])

    tableData.append(
        [Paragraph('''<p>Модуль деформации после динамического нагружения E<sub rise="0.5" size="6">50d</sub>, МПа:</p>''', LeftStyle), "",
         "", "", Ed, ""])

    tableData.append(
        [Paragraph('''<p>Коэффициент снижения жесткости K<sub rise="0.5" size="6">d</sub>, д.е.:</p>''', LeftStyle), "",
         "", "", Kd, ""])
    tableData.append(
        [Paragraph('''<p>Дополнительная деформация виброползучести на период 50 лет, %''', LeftStyle), "",
         "", "", prediction, ""])
    t = Table(tableData, colWidths=175/6 * mm, rowHeights=4 * mm)
    t.setStyle([('SPAN', (0, 0), (-1, 0)),
                ('SPAN', (0, 1), (-1, r)),

                ('SPAN', (0, -1), (3, -1)),
                ('SPAN', (-2, -1), (-1, -1)),

                ('SPAN', (0, -3), (3, -3)),
                ('SPAN', (-2, -3), (-1, -3)),

                ('SPAN', (0, -2), (3, -2)),
                ('SPAN', (-2, -2), (-1, -2)),

                ('SPAN', (0, -4), (3, -4)),
                ('SPAN', (-2, -4), (-1, -4)),
                #('SPAN', (2, -1), (3, -1)),
                #('SPAN', (4, -1), (5, -1)),
                #('SPAN', (2, -2), (3, -2)),
                #('SPAN', (4, -2), (5, -2)),
                #('SPAN', (2, -3), (3, -3)),
              #  ('SPAN', (4, -3), (5, -3)),

                ("BACKGROUND", (0, -1), (3, -1), HexColor(0xebebeb)),
                ("BACKGROUND", (0, -2), (3, -2), HexColor(0xebebeb)),
                ("BACKGROUND", (0, -3), (3, -3), HexColor(0xebebeb)),
                ("BACKGROUND", (0, -4), (3, -4), HexColor(0xebebeb)),

                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                #("LEFTPADDING", (0, 1), (1, 10), 50 * mm),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, r), "CENTER"),
                ("ALIGN", (0, r+1), (0, -1), "LEFT"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, (38-((r-30)*4)) * mm)

def result_table_CF(canvas, Res, pick, scale = 0.8):


    try:
        a = svg2rlg(pick[0])
        a.scale(scale, scale)
        renderPDF.draw(a, canvas, 36 * mm, 65 * mm)
        b = svg2rlg(pick[1])
        b.scale(scale, scale)
        renderPDF.draw(b, canvas, 120 * mm, 133 * mm)
    except AttributeError:
        a = ImageReader(pick[0])
        #canvas.drawImage(a, 31 * mm, 81 * mm,
                            # width=80* mm, height=80 * mm)
        b = ImageReader(pick[1])
        canvas.drawImage(b, 115 * mm, 81 * mm,
                             width=80 * mm, height=40 * mm)


    tableData = [["РЕЗУЛЬТАТЫ ИСПЫТАНИЯ", "", "", "", "", ""]]
    r = 21
    table_move = 3
    for i in range(table_move):
        tableData.append([""])


    tableData.append(["Напряжение, МПа", "", "", "", "", ""])
    tableData.append([Paragraph('''<p>σ<sub rise="0.5" size="5">3c</sub></p>''', CentralStyle),
                      Paragraph('''<p>σ<sub rise="0.5" size="5">1c</sub></p>''', CentralStyle),
                      Paragraph('''<p>σ<sub rise="0.5" size="5">1f</sub></p>''', CentralStyle), "", "", ""])

    tableData.append([zap(Res["sigma_3_mohr"][0], 3), zap(Res["sigma_3_mohr"][0], 3), zap(Res["sigma_1_mohr"][0], 3), "", "", ""])
    tableData.append([zap(Res["sigma_3_mohr"][1], 3), zap(Res["sigma_3_mohr"][1], 3), zap(Res["sigma_1_mohr"][1], 3), "", "", ""])
    tableData.append([zap(Res["sigma_3_mohr"][2], 3), zap(Res["sigma_3_mohr"][2], 3), zap(Res["sigma_1_mohr"][2], 3), "", "", ""])

    for i in range(r):
        tableData.append([""])

    tableData.append(
        [Paragraph('''<p>Эффективное сцепление с', МПа:</p>''', LeftStyle), "", "", "",
         zap(Res["c"], 3), ""])
    tableData.append(
        [Paragraph('''<p>Эффективный угол внутреннего трения φ', град:</p>''', LeftStyle), "", "", "",
         zap(Res["fi"], 1), ""])

    t = Table(tableData, colWidths=175/6 * mm, rowHeights = 4 * mm)
    t.setStyle([('SPAN', (0, 0), (-1, 0)),

                ('SPAN', (0, 1), (-1, table_move)),

                ('SPAN', (0, table_move+1), (2, table_move+1)),
                ('SPAN', (3, 1), (-1, -4)),

                ('SPAN', (0, 6+table_move), (-1, r+table_move+5)),

                ('SPAN', (0, -1), (3, -1)),
                ('SPAN', (-2, -1), (-1, -1)),
                #('SPAN', (2, -1), (3, -1)),
                #('SPAN', (4, -1), (5, -1)),
                ('SPAN', (0, -2), (3, -2)),
                ('SPAN', (-2, -2), (-1, -2)),
                #('SPAN', (2, -2), (3, -2)),
                #('SPAN', (4, -2), (5, -2)),
                #('SPAN', (2, -3), (3, -3)),
              #  ('SPAN', (4, -3), (5, -3)),

                ("BACKGROUND", (0, -1), (3, -1), HexColor(0xebebeb)),
                ("BACKGROUND", (0, -2), (3, -2), HexColor(0xebebeb)),

                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                #("LEFTPADDING", (0, 1), (1, 10), 50 * mm),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, r), "CENTER"),
                ("ALIGN", (0, r+1), (0, -1), "LEFT"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, ((34-((r - 30)*4)) - table_move*6) * mm)

def result_table_CF_KN(canvas, Res, pick, scale = 0.8):


    try:
        a = svg2rlg(pick[0])
        a.scale(scale, scale)
        renderPDF.draw(a, canvas, 36 * mm, 65 * mm)
        b = svg2rlg(pick[1])
        b.scale(scale, scale)
        renderPDF.draw(b, canvas, 120 * mm, 133 * mm)
    except AttributeError:
        a = ImageReader(pick[0])
        #canvas.drawImage(a, 31 * mm, 81 * mm,
                            # width=80* mm, height=80 * mm)
        b = ImageReader(pick[1])
        canvas.drawImage(b, 115 * mm, 81 * mm,
                             width=80 * mm, height=40 * mm)


    tableData = [["РЕЗУЛЬТАТЫ ИСПЫТАНИЯ", "", "", "", "", "", "", ""]]
    r = 21
    table_move = 3
    for i in range(table_move):
        tableData.append([""])


    tableData.append(["Напряжение, МПа", "", "", "", "", "", "", ""])
    tableData.append([Paragraph('''<p>σ<sub rise="0.5" size="5">3c</sub></p>''', CentralStyle),
                      Paragraph('''<p>σ<sub rise="0.5" size="5">1c</sub></p>''', CentralStyle),
                      Paragraph('''<p>σ<sub rise="0.5" size="5">1f</sub></p>''', CentralStyle),
                      Paragraph('''<p>u<sub rise="0.5" size="5">f</sub></p>''', CentralStyle), "", "", "", ""])

    tableData.append([zap(Res["sigma_3_mohr"][0], 3), zap(Res["sigma_3_mohr"][0], 3), zap(Res["sigma_1_mohr"][0], 3), zap(Res["u_mohr"][0], 3) if Res["u_mohr"][0] != 0 else "-", "", "", "", ""])
    tableData.append([zap(Res["sigma_3_mohr"][1], 3), zap(Res["sigma_3_mohr"][1], 3), zap(Res["sigma_1_mohr"][1], 3), zap(Res["u_mohr"][1], 3) if Res["u_mohr"][1] != 0 else "-", "", "", "", ""])
    tableData.append([zap(Res["sigma_3_mohr"][2], 3), zap(Res["sigma_3_mohr"][2], 3), zap(Res["sigma_1_mohr"][2], 3), zap(Res["u_mohr"][2], 3) if Res["u_mohr"][2] != 0 else "-", "", "", "", ""])

    for i in range(r):
        tableData.append([""])

    tableData.append(
        [Paragraph('''<p>Эффективное сцепление с', МПа:</p>''', LeftStyle), "", "", "",
         zap(Res["c"], 3), "", "", ""])
    tableData.append(
        [Paragraph('''<p>Эффективный угол внутреннего трения φ', град:</p>''', LeftStyle), "", "", "",
         zap(Res["fi"], 1), "", "", ""])

    t = Table(tableData, colWidths=175/8 * mm, rowHeights = 4 * mm)
    t.setStyle([('SPAN', (0, 0), (-1, 0)),

                ('SPAN', (0, 1), (-1, table_move)),

                ('SPAN', (0, table_move+1), (3, table_move+1)),
                ('SPAN', (4, 1), (-1, -3)),

                ('SPAN', (0, 6+table_move), (-1, r+table_move+5)),

                ('SPAN', (0, -1), (3, -1)),
                ('SPAN', (-4, -1), (-1, -1)),
                #('SPAN', (2, -1), (3, -1)),
                #('SPAN', (4, -1), (5, -1)),
                ('SPAN', (0, -2), (3, -2)),
                ('SPAN', (-4, -2), (-1, -2)),
                #('SPAN', (2, -2), (3, -2)),
                #('SPAN', (4, -2), (5, -2)),
                #('SPAN', (2, -3), (3, -3)),
              #  ('SPAN', (4, -3), (5, -3)),

                ("BACKGROUND", (0, -1), (3, -1), HexColor(0xebebeb)),
                ("BACKGROUND", (0, -2), (3, -2), HexColor(0xebebeb)),

                ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
                ("FONTNAME", (0, 1), (-1, -1), 'Times'),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                #("LEFTPADDING", (0, 1), (1, 10), 50 * mm),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, r), "CENTER"),
                ("ALIGN", (0, r+1), (0, -1), "LEFT"),
                ('BOX', (0, 1), (-1, -1), 0.3 * mm, "black"),
                ('INNERGRID', (0, 1), (-1, -1), 0.3 * mm, "black")])

    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, ((34-((r - 30)*4)) - table_move*6) * mm)





def result_table_statment_cyclic(canvas, Data):
    d = []

    d.append(["Лаб. №", "", "", "Скв. №", "", "", "Глубина отбора, м", "", "",
              "Наименование грунта", "", "", "", "", "", "", "", "",
              Paragraph('''<p>σ<sub rise="0.5" size="6">3</sub>, кПа</p>''', CentralStyle), "",
              Paragraph('''<p>σ<sub rise="0.5" size="6">1</sub>, кПа</p>''', CentralStyle), "",
              Paragraph('''<p>τ<sub rise="0.5" size="6">α</sub>, кПа</p>''', CentralStyle), "",
              Paragraph('''<p>PPR<sub rise="0.5" size="6">max</sub></p>''', CentralStyle), "",
              Paragraph('''<p>ε<sub rise="0.5" size="6">max</sub></p>''', CentralStyle), "",
              Paragraph('''<p>n<sub rise="0.5" size="6">c</sub>, ед.</p>''', CentralStyle), ""])

    style = [("FONTNAME", (0, 0), (-1, -1), 'Times'),
             ("FONTSIZE", (0, 0), (-1, -1), 8),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("ALIGN", (0, 0), (-1, -1), "CENTER"),
             ('BOX', (0, 0), (-1, -1), 1, "black"),
             ('INNERGRID', (0, 0), (-1, -1), 1, "black"),
             ('SPAN', (0, 0), (2, 0)),
             ('SPAN', (3, 0), (5, 0)),
             ('SPAN', (6, 0), (8, 0)),
             ('SPAN', (9, 0), (17, 0)),
             ('SPAN', (18, 0), (19, 0)),
             ('SPAN', (20, 0), (21, 0)),
             ('SPAN', (22, 0), (23, 0)),
             ('SPAN', (24, 0), (25, 0)),
             ('SPAN', (26, 0), (27, 0)),
             ('SPAN', (28, 0), (29, 0))]

    add = 0
    for i, key in enumerate(Data):
        d.append([Paragraph(key, CentralStyle), "", "", Paragraph(Data[key]["borehole"], CentralStyle), "", "",
                  Data[key]["depth"], "", "",
                  Paragraph(Data[key]["name"], CentralStyle), "", "", "", "", "", "", "", "",
                  Data[key]["sigma3"], "",
                  Data[key]["sigma1"], "",
                  Data[key]["tau"], "",
                  Data[key]["PPRmax"], "",
                  Data[key]["EPSmax"], "",
                  Data[key]["Nc"], ""])

        koef = max([round(GetTextDimensions(key, 8, "Times New Roman") // 22),
                    round(GetTextDimensions(Data[key]["name"], 8, "Times New Roman") // 70),
                    round(GetTextDimensions(Data[key]["borehole"], 8, "Times New Roman") // 22)])
        if koef >= 1:
            for ll in range(koef):
                d.append(["" for k in range(30)])
            style += list(map(lambda m, n: ('SPAN', (m, i + add + 1), (n, i + add + 1 + koef)),
                              [0, 3, 6, 9, 18, 20, 22, 24, 26, 28], [2, 5, 8, 17, 19, 21, 23, 25, 27, 29]))
            add += koef
        else:
            style += list(
                map(lambda m, n: ('SPAN', (m, i + add + 1), (n, i + add + 1)), [0, 3, 6, 9, 18, 20, 22, 24, 26, 28],
                    [2, 5, 8, 17, 19, 21, 23, 25, 27, 29]))

    t = Table(d, colWidths=8.75 * mm, rowHeights=5 * mm)
    t.setStyle(style)
    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, (71) * mm)


def ResultStampPart1(canvas, M):
    s1 = ["№ исп."]
    s2 = ["Время, ч"]
    span = []
    for m in range(1, len(M)):
        s1.append(str(m))
        # zap(str1(wb["Лист1"]['Z' + str(6 + Nop)].value).replace(".", ","), 2)
        s1.append("")
        s2.append("l, мм")
        s2.append(Paragraph(
            '''<p>C<sub rise="0.5" size="6">eq</sub>, МПа</p>''', CentralStyle))
    #'''<p>C<sup rise="2.5" size="5">8</sup><sub rise="0.5" size="6">eq</sub>, МПа</p>'''
    #'''<p><font size = "6" color = "black" face = "Times" >C<sub>eq</sub>, МПа</font></p>'''
    for i in range(len(s1)):
        if i % 2 == 0 and i != 0:
            span.append(('SPAN', (i, 1), (i - 1, 1)))

    for i in range(len(s1)):
        span.append(('SPAN', (i, 2), (i, 3)))


    D = [list() for i in range(len(M[0]) + 4)]
    D[0] = ["РЕЗУЛЬТАТЫ ИСПЫТАНИЯ"]
    D[1] = s1
    D[2] = s2
    D[3] = [""]

    def sy(i, M):
        s = []
        for j in range(len(M)):
            try:

                if j == 0:
                    try:
                        m = round(M[j][i])
                        s.append(zap(str(M[j][i]).replace(".", ","), 2))

                    except TypeError:
                        s.append(str(M[j][i]))
                else:
                    try:
                        s.append(str(round(M[j][0][i], 3)).replace(".", ","))
                        s.append(str(round(M[j][1][i], 3)).replace(".", ","))
                    except TypeError:
                        s.append(str(M[j][0][i]))
                        s.append(str(M[j][1][i]))
            except IndexError:
                pass
        return s

    for i in range(len(M[0])):
        D[i + 4] = sy(i, M)

    Fsize = 8
    if len(M) > 7:
        Fsize = Fsize - (len(M) - 7)

    tstyle = [('SPAN', (0, 0), (-1, 0)),
              ("BACKGROUND", (0, 1), (-1, 3), HexColor(0xebebeb)),
              ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
              ("FONTNAME", (0, 1), (-1, -1), 'Times'),
              ("FONTSIZE", (0, 0), (-1, -1), Fsize),
              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("ALIGN", (0, 0), (-1, -1), "CENTER"),
              ('BOX', (0, 1), (-1, -1), 0.3 *mm, "black"),
              ('INNERGRID', (0, 1), (-1, -1), 0.3 *mm, "black")]
    st = span + tstyle

    t = Table(D, colWidths=175 / (2 * (len(M) - 1) + 1) * mm, rowHeights= 4 * mm)
    t.setStyle(st)
    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, (163 - (4 * int(len(M[0])))) * mm)

def ResultStampPart2(canvas, R):

    #D = [["РЕЗУЛЬТАТЫ ИСПЫТАНИЯ"], [Paragraph('''<p>№ исп</p>''', CentralStyle),
    D = [[Paragraph('''<p>№ исп</p>''', CentralStyle),
    Paragraph('''<p>C<sup rise="2.5" size="5">8</sup><sub rise="0.5" size="6">eq</sub>, МПа</p>''', CentralStyle),
    Paragraph('''<p>C<sup rise="2.5" size="6">дл</sup><sub rise="0.5" size="6">eq</sub>, МПа</p>''', CentralStyle),
    Paragraph('''<p>K<sub rise="0.5" size="6">п</sub>, е.д.</p>''', CentralStyle),
    Paragraph('''<p>C<sup rise="2.5" size="6">дл</sup><sub rise="0.5" size="6">eq расчетное</sub>, МПа</p>''', CentralStyle)]]


    for i in range(len(R)):
        D.append(R[i])

    st = [#('SPAN', (0, 0), (-1, 0)),
          ("FONTNAME", (0, 0), (-1, 0), 'TimesDj'),
          ("FONTNAME", (0, 1), (-1, -1), 'Times'),
          ("FONTSIZE", (0, 0), (-1, -1), 8),
          ('SPAN', (3, 2), (3, -2)),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("ALIGN", (0, 0), (-1, -1), "CENTER"),
          ('BOX', (0, 0), (-1, -1), 0.3 * mm, "black"),
          ("BACKGROUND", (0, 0), (-1, 0), HexColor(0xebebeb)),
          ('INNERGRID', (0, 0), (-1, -1), 0.3 * mm, "black")]

    t = Table(D, colWidths=35 * mm, rowHeights=4 * mm)
    t.setStyle(st)
    t.wrapOn(canvas, 0, 0)
    t.drawOn(canvas, 25 * mm, (65 + 4 * (10 - len(R))) * mm) #131



def report_rc(Name, Data_customer, Data_phiz, Lab, path, test_parameter, res, picks, version = 1.1):  # p1 - папка сохранения отчета, p2-путь к файлу XL, Nop - номер опыта


    # Подгружаем шрифты
    pdfmetrics.registerFont(TTFont('Times', path + 'Report Data/Times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesK', path + 'Report Data/TimesK.ttf'))
    pdfmetrics.registerFont(TTFont('TimesDj', path + 'Report Data/TimesDj.ttf'))

    # Загружаем документ эксель, проверяем изменялось ли имя документа и создаем отчет


    canvas = Canvas(Name, pagesize=A4)


    test_parameter.h = 100
    test_parameter.d = 50
    test_parameter.Rezhim = "Статическое нагружение"
    test_parameter.Oborudovanie = "АСИС ГТ.2.0.5"

    code = SaveCode(version)

    main_frame(canvas, path,  Data_customer, code, "1/1")
    sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                                ["ИСПЫТАНИЯ ГРУНТА МЕТОДОМ МАЛОАМПЛИТУДНЫХ ДИНАМИЧЕСКИХ",
                                "КОЛЕБАНИЙ В РЕЗОНАНСНОЙ КОЛОНКЕ (ГОСТ Р 56353-2015)"], "/РК")

    parameter_table(canvas, Data_phiz, Lab)
    test_mode_rc(canvas, Data_phiz.r, test_parameter)
    result_table_rc(canvas, res, picks)


    canvas.showPage()

    canvas.save()

def report_triaxial_cyclic(Name, Data_customer, Data_phiz, Lab, path, test_parameter, res, picks, version = 1.1):  # p1 - папка сохранения отчета, p2-путь к файлу XL, Nop - номер опыта
    # Подгружаем шрифты
    pdfmetrics.registerFont(TTFont('Times', path + 'Report Data/Times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesK', path + 'Report Data/TimesK.ttf'))
    pdfmetrics.registerFont(TTFont('TimesDj', path + 'Report Data/TimesDj.ttf'))

    canvas = Canvas(Name, pagesize=A4)

    code = SaveCode(version)

    main_frame(canvas, path,  Data_customer, code, "1/2")
    if test_parameter["type"] == "Сейсморазжижение":
        sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                                ["ОПРЕДЕЛЕНИЕ СЕЙСМИЧЕСКОЙ РАЗЖИЖАЕМОСТИ ГРУНТОВ МЕТОДОМ ЦИКЛИЧЕСКИХ",
                                "ТРЁХОСНЫХ СЖАТИЙ С РЕГУЛИРУЕМОЙ НАГРУЗКОЙ (ГОСТ 56353-2015, ASTM D5311/ASTM D5311M-13)"], "/С")
    elif test_parameter["type"] == "Штормовое разжижение":
        sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                                ["ОПРЕДЕЛЕНИЕ РАЗЖИЖАЕМОСТИ ГРУНТОВ МЕТОДОМ ЦИКЛИЧЕСКИХ ТРЁХОСНЫХ СЖАТИЙ С",
                                 "РЕГУЛИРУЕМОЙ НАГРУЗКОЙ (ШТОРМОВОЕ ВОЗДЕЙСТВИЕ) (ГОСТ 56353-2015, ASTM D5311/ASTM D5311M-13)"], "/ШТ")
    parameter_table(canvas, Data_phiz, Lab)
    test_mode_triaxial_cyclic(canvas, Data_phiz.r, test_parameter)
    result_table__triaxial_cyclic(canvas, res, [picks[0], picks[1]])


    canvas.showPage()

    main_frame(canvas, path, Data_customer, code, "2/2")
    if test_parameter["type"] == "Сейсморазжижение":
        sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                                ["ОПРЕДЕЛЕНИЕ СЕЙСМИЧЕСКОЙ РАЗЖИЖАЕМОСТИ ГРУНТОВ МЕТОДОМ ЦИКЛИЧЕСКИХ",
                                 "ТРЁХОСНЫХ СЖАТИЙ С РЕГУЛИРУЕМОЙ НАГРУЗКОЙ (ГОСТ 56353-2015, ASTM D5311/ASTM D5311M-13)"], "/С")
    elif test_parameter["type"] == "Штормовое разжижение":
        sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                                ["ОПРЕДЕЛЕНИЕ РАЗЖИЖАЕМОСТИ ГРУНТОВ МЕТОДОМ ЦИКЛИЧЕСКИХ ТРЁХОСНЫХ СЖАТИЙ С",
                                 "РЕГУЛИРУЕМОЙ НАГРУЗКОЙ (ШТОРМОВОЕ ВОЗДЕЙСТВИЕ) (ГОСТ 56353-2015, ASTM D5311/ASTM D5311M-13)"],
                                "/ШТ")
    parameter_table(canvas, Data_phiz, Lab)
    test_mode_triaxial_cyclic(canvas, Data_phiz.r, test_parameter)
    result_table__triaxial_cyclic(canvas, res, [picks[2]])

    canvas.showPage()

    canvas.save()

def report_consolidation(Name, Data_customer, Data_phiz, Lab, path, test_parameter, res, picks, version = 1.1):  # p1 - папка сохранения отчета, p2-путь к файлу XL, Nop - номер опыта
    # Подгружаем шрифты
    pdfmetrics.registerFont(TTFont('Times', path + 'Report Data/Times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesK', path + 'Report Data/TimesK.ttf'))
    pdfmetrics.registerFont(TTFont('TimesDj', path + 'Report Data/TimesDj.ttf'))

    canvas = Canvas(Name, pagesize=A4)

    code = SaveCode(version)

    #main_frame(canvas, path,  Data_customer, code, "1/2")
    #sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                                #["ОПРЕДЕЛЕНИЕ ПАРАМЕТРОВ КОНСОЛИДАЦИИ ГРУНТОВ",
                                #"МЕТОДОМ ТРЕХОСНОГО СЖАТИЯ (ГОСТ 12248-2010)"], "-К")
    #sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                            #["ИСПЫТАНИЯ ГРУНТОВ МЕТОДОМ ТРЕХОСНОГО",
                             #"СЖАТИЯ (ГОСТ 12248-2010)"], "-ТД")

    #parameter_table(canvas, Data_phiz, Lab)
    #test_mode_consolidation(canvas, test_parameter)

    #result_table_consolidation(canvas, res, [picks[0], picks[1]])

    #canvas.showPage()
    main_frame(canvas, path, Data_customer, code, "1/1")
    sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                            ["ОПРЕДЕЛЕНИЕ ПАРАМЕТРОВ КОНСОЛИДАЦИИ ГРУНТОВ МЕТОДОМ",
                             "КОМПРЕССИОННОГО СЖАТИЯ (ГОСТ 12248.3-2020)"], "/ВК")

    parameter_table(canvas, Data_phiz, Lab)
    test_mode_consolidation_1(canvas, test_parameter)

    result_table_deviator(canvas, res, [picks[0], picks[1]])

    canvas.showPage()

    canvas.save()

def report_FCE(Name, Data_customer, Data_phiz, Lab, path, test_parameter, res, picks, version = 1.1):  # p1 - папка сохранения отчета, p2-путь к файлу XL, Nop - номер опыта
    # Подгружаем шрифты
    pdfmetrics.registerFont(TTFont('Times', path + 'Report Data/Times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesK', path + 'Report Data/TimesK.ttf'))
    pdfmetrics.registerFont(TTFont('TimesDj', path + 'Report Data/TimesDj.ttf'))

    K0 = test_parameter["K0"]

    canvas = Canvas(Name, pagesize=A4)

    code = SaveCode(version)

    main_frame(canvas, path, Data_customer, code, "1/2")
    sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                            ["ИСПЫТАНИЯ ГРУНТОВ МЕТОДОМ ТРЕХОСНОГО",
                             "СЖАТИЯ (ГОСТ 12248.3-2020)"], "/ТД")

    parameter_table(canvas, Data_phiz, Lab)
    test_parameter["K0"] = K0[0]
    test_mode_consolidation(canvas, test_parameter)

    result_table_deviator1(canvas, res, [picks[0], picks[1]])

    canvas.showPage()

    main_frame(canvas, path, Data_customer, code, "2/2")
    sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                            ["ИСПЫТАНИЯ ГРУНТОВ МЕТОДОМ ТРЕХОСНОГО",
                             "СЖАТИЯ (ГОСТ 12248.3-2020)"], "/ТД")

    parameter_table(canvas, Data_phiz, Lab)
    test_parameter["K0"] = K0[1]
    test_parameter["sigma_3"] = zap(res["sigma_3_mohr"][0], 3) + "/" + zap(res["sigma_3_mohr"][1], 3) + "/" + zap(res["sigma_3_mohr"][2], 3)
    test_mode_consolidation(canvas, test_parameter)

    result_table_CF(canvas, res, [picks[2], picks[3]])

    canvas.save()

def report_FC(Name, Data_customer, Data_phiz, Lab, path, test_parameter, res, picks, version = 1.1):  # p1 - папка сохранения отчета, p2-путь к файлу XL, Nop - номер опыта
    # Подгружаем шрифты
    pdfmetrics.registerFont(TTFont('Times', path + 'Report Data/Times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesK', path + 'Report Data/TimesK.ttf'))
    pdfmetrics.registerFont(TTFont('TimesDj', path + 'Report Data/TimesDj.ttf'))
    test_parameter["K0"] = test_parameter["K0"][1]
    name = "ТД"
    canvas = Canvas(Name, pagesize=A4)

    code = SaveCode(version)

    main_frame(canvas, path, Data_customer, code, "1/1")
    sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                            ["ИСПЫТАНИЯ ГРУНТОВ МЕТОДОМ ТРЕХОСНОГО",
                             "СЖАТИЯ (ГОСТ 12248.3-2020)"], "/" + name)

    parameter_table(canvas, Data_phiz, Lab)
    test_parameter["sigma_3"] = zap(res["sigma_3_mohr"][0], 3) + "/" + zap(res["sigma_3_mohr"][1], 3) + "/" + zap(res["sigma_3_mohr"][2], 3)
    test_mode_consolidation(canvas, test_parameter)

    result_table_CF(canvas, res, [picks[0],picks[1]])

    canvas.save()

def report_FC_KN(Name, Data_customer, Data_phiz, Lab, path, test_parameter, res, picks, version = 1.1):  # p1 - папка сохранения отчета, p2-путь к файлу XL, Nop - номер опыта
    # Подгружаем шрифты
    pdfmetrics.registerFont(TTFont('Times', path + 'Report Data/Times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesK', path + 'Report Data/TimesK.ttf'))
    pdfmetrics.registerFont(TTFont('TimesDj', path + 'Report Data/TimesDj.ttf'))
    test_parameter["K0"] = test_parameter["K0"][1]
    test_parameter["mode"] = "КН, девиаторное нагружение в кинематическом режиме"
    name = "КН"

    canvas = Canvas(Name, pagesize=A4)

    code = SaveCode(version)

    main_frame(canvas, path, Data_customer, code, "1/1")
    sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                            ["ИСПЫТАНИЯ ГРУНТОВ МЕТОДОМ ТРЕХОСНОГО",
                             "СЖАТИЯ (ГОСТ 12248.3-2020)"], "/" + name)

    parameter_table(canvas, Data_phiz, Lab)
    test_parameter["sigma_3"] = zap(res["sigma_3_mohr"][0], 3) + "/" + zap(res["sigma_3_mohr"][1], 3) + "/" + zap(res["sigma_3_mohr"][2], 3)
    test_mode_consolidation(canvas, test_parameter)

    result_table_CF_KN(canvas, res, [picks[0],picks[1]])

    canvas.save()

def report_VibrationCreep(Name, Data_customer, Data_phiz, Lab, path, test_parameter, res_static, res_dynamic,  picks, version = 1.1):  # p1 - папка сохранения отчета, p2-путь к файлу XL, Nop - номер опыта
    # Подгружаем шрифты
    pdfmetrics.registerFont(TTFont('Times', path + 'Report Data/Times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesK', path + 'Report Data/TimesK.ttf'))
    pdfmetrics.registerFont(TTFont('TimesDj', path + 'Report Data/TimesDj.ttf'))

    canvas = Canvas(Name, pagesize=A4)

    code = SaveCode(version)

    main_frame(canvas, path, Data_customer, code, "1/2")
    sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                            ["ОПРЕДЕЛЕНИЕ ПАРАМЕТРОВ ВИБРОПОЛЗУЧЕСТИ ГРУНТОВ МЕТОДОМ ЦИКЛИЧЕСКИХ ТРЁХОСНЫХ",
                             "СЖАТИЙ С РЕГУЛИРУЕМОЙ НАГРУЗКОЙ (ГОСТ 56353-2020 п. Д3, ASTM D5311/ASTM D5311M-13)"], "/ВП")

    parameter_table(canvas, Data_phiz, Lab)
    test_mode_vibration_creep(canvas, test_parameter)

    result_table_deviator_vc(canvas, res_static, [picks[2], picks[3]])

    canvas.showPage()

    main_frame(canvas, path, Data_customer, code, "2/2")
    sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                            ["ОПРЕДЕЛЕНИЕ ПАРАМЕТРОВ ВИБРОПОЛЗУЧЕСТИ ГРУНТОВ МЕТОДОМ ЦИКЛИЧЕСКИХ ТРЁХОСНЫХ",
                             "СЖАТИЙ С РЕГУЛИРУЕМОЙ НАГРУЗКОЙ (ГОСТ 56353-2020 п. Д3, ASTM D5311/ASTM D5311M-13)"], "/ВП")

    parameter_table(canvas, Data_phiz, Lab)
    test_mode_vibration_creep(canvas, test_parameter)

    result_vibration_creep(canvas, res_dynamic, [picks[0], picks[1]])

    canvas.save()

def report_cyclic_damping(Name, Data_customer, Data_phiz, Lab, path, test_parameter, res, picks, version = 1.1):  # p1 - папка сохранения отчета, p2-путь к файлу XL, Nop - номер опыта
    # Подгружаем шрифты
    pdfmetrics.registerFont(TTFont('Times', path + 'Report Data/Times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesK', path + 'Report Data/TimesK.ttf'))
    pdfmetrics.registerFont(TTFont('TimesDj', path + 'Report Data/TimesDj.ttf'))

    canvas = Canvas(Name, pagesize=A4)

    code = SaveCode(version)

    main_frame(canvas, path,  Data_customer, code, "1/1")
    sample_identifier_table(canvas, Data_customer, Data_phiz, Lab,
                            ["ОПРЕДЕЛЕНИЕ ДЕМПФИРУЮЩИХ СВОЙСТ ГРУНТОВ МЕТОДОМ ЦИКЛИЧЕСКИХ",
                             "ТРЁХОСНЫХ СЖАТИЙ С РЕГУЛИРУЕМОЙ НАГРУЗКОЙ (ГОСТ 56353-2015, ASTM D5311/ASTM D5311M-13)"],
                            "/Д")
    parameter_table(canvas, Data_phiz, Lab)
    test_mode_triaxial_cyclic(canvas, Data_phiz.r, test_parameter)
    result_table_cyclic_damping(canvas, res, [picks[0]])

    canvas.showPage()

    canvas.save()




def StampReport(M, R, p1, p2, Nop, path, version = 1):  # p1 - папка сохранения отчета, p2-путь к файлу XL, Nop - номер опыта


    # Подгружаем шрифты
    pdfmetrics.registerFont(TTFont('Times', path + 'Report Data/Times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesK', path + 'Report Data/TimesK.ttf'))
    pdfmetrics.registerFont(TTFont('TimesDj', path + 'Report Data/TimesDj.ttf'))

    # Загружаем документ эксель, проверяем изменялось ли имя документа и создаем отчет
    wb = load_workbook(p2, data_only=True)

    path2 = "//192.168.0.1/files/Прикладные программы/"
    path3 = "Z:/files/Прикладные программы/"
    path = path2

    canvas = Canvas(p1+"/Отчет.pdf", pagesize=A4)





    name = ["ИСПЫТАНИЕ ШАРИКОВЫМ ШТАМПОМ (ГОСТ 12248.3-2020)",""]
    Data = {}
    Data["Rezhim"] = "Статическое нагружение"
    Data["Oborudovanie"] = "Оборудование: АСИС ГТ.2.0.5"
    Data["h"] = 71.4
    Data["d"] = 35

    code = SaveCode(version)
    data = str_for_excel(wb["Лист1"]["Q1"].value)
    accreditation = str_for_excel(wb["Лист1"]["I2"].value)

    if accreditation == "ООО":
        accreditation = "ON"
    elif accreditation== "ОАО" or accreditation== "АО":
        accreditation = "AN"





    # Лист 1

    main_frame(canvas, path, accreditation, code, data, "1/1")
    sample_identifier_table(canvas, wb, Nop, name, "/ШШ")
    parameter_table_ice(canvas, wb, Nop)
    testModeStamm(canvas, wb, Nop, Data)
    ResultStampPart1(canvas, M)
    ResultStampPart2(canvas, R)
    canvas.showPage()

    canvas.save()


def StatmentReport(name, Data, path):  # p1 - папка сохранения отчета, p2-путь к файлу XL, Nop - номер опыта

    # Подгружаем шрифты
    pdfmetrics.registerFont(TTFont('Times', path + 'Report Data/Times.ttf'))
    pdfmetrics.registerFont(TTFont('TimesK', path + 'Report Data/TimesK.ttf'))
    pdfmetrics.registerFont(TTFont('TimesDj', path + 'Report Data/TimesDj.ttf'))

    # Загружаем документ эксель, проверяем изменялось ли имя документа и создаем отчет

    canvas = Canvas(name, pagesize=(landscape(A4)))

    # Заполняем лист
    canvas.setLineWidth(0.5 * mm)
    canvas.rect(20 * mm, 5 * mm, 272 * mm, 200 * mm)  # Основная рамка

    result_table_statment_cyclic(canvas, Data)


    # Сохраняем документ
    canvas.showPage()
    canvas.save()




if __name__ == '__main__':
    print(cm)
    '''path2 = "//192.168.0.1/files/Прикладные программы/"
    path3 = "Z:/files/Прикладные программы/"
    path = path2
    Nop = 2
    Akred = "AN"
    p1 = "C:/Users/Пользователь/Desktop/Новая папка (2)/Новая папка (2)"
    p2 = "C:/Users/Пользователь/Desktop/Новая папка (2)/Новая папка (2)/Образец ведомости.xlsx"
    M = [[0.02, 0.08, 0.17, 0.25, 0.33, 0.5, 1, 2, 4, 8, '...', 26], [
        [0.5185186, 0.6084657, 0.6465609, 0.6598639, 0.6657329352941176, 0.6793650999999999, 0.7054411268656716,
         0.7173721166666667, 0.7325765145695364, 0.7563925171548117, '...', 0.7873782045020464],
        [0.09836396506228601, 0.0884800453456501, 0.08326682409541425, 0.08250831291552266, 0.08149479323937826,
         0.07997605411287687, 0.07715619486880514, 0.07533563520983763, 0.07419445120256152, 0.07213222369517026, '...',
         0.06845857378844353]], [[0.5185186, 0.6084657, 0.6465609, 0.6598639, 0.6657329352941176, 0.6793650999999999, 0.7054411268656716,
              0.7173721166666667, 0.7325765145695364, 0.7563925171548117, '...', 0.7873782045020464],[0.09836396506228601, 0.0884800453456501, 0.08326682409541425, 0.08250831291552266, 0.08149479323937826,
              0.07997605411287687, 0.07715619486880514, 0.07533563520983763, 0.07419445120256152, 0.07213222369517026,
              '...', 0.06845857378844353]], [[0.3809524, 0.45855376666666664, 0.47971783333333334, 0.4920635, 0.5015873, 0.5140629789473684,
              0.5308641833333333, 0.5412663006802721, 0.552496740625, 0.5649834725212465],[0.13202479794421462, 0.1174062381356648, 0.1122265402417589, 0.10941082345525065, 0.10733340482757983,
              0.1047285545391993, 0.10252601817537872, 0.09985677163422917, 0.10000753362116065, 0.09577979975504072]],[[0.3650794, 0.4497355, 0.4772487, 0.48941799999999996, 0.4965986857142857, 0.506974559090909,
           0.5227771999999999, 0.5238096, 0.5450685058295963, 0.5586246996978852],[0.13970535027324316, 0.11970830127324335, 0.11280716474926536, 0.11000223270756844, 0.10841162950287685,
           0.10619284885579205, 0.10298282466655533, 0.10305032418441566, 0.09878286004707958, 0.09710987898258577]], [[0.5343916, 0.6014109666666666, 0.62433865, 0.6349207, 0.6402117, 0.67063495, 0.6838988559633027,
              0.6972766349693251, 0.7037038],[0.0980934376418138, 0.08951794315568584, 0.08623056209522303, 0.084793380854133, 0.08409260987775251,
              0.08027776173501357, 0.07962357189217556, 0.07822641948679973, 0.07751195111558946]], [[0.2486773, 0.30511463333333333, 0.32804235000000004, 0.34060845624999997, 0.351851875, 0.3672316711864407,
              0.3791666875, 0.38799604375, 0.3981769950155763],[0.21079651858416149, 0.17644867484430518, 0.16519593776950944, 0.15871139149222033, 0.15301061768470814,
              0.14853145527789252, 0.14447499695691826, 0.14088489087613515, 0.13698796070154876]]]
    R = [[1, 0.13690691777230923, 0.11673061401456442, 0.8526275802125635, 0.12786124522291376],
         [1, 0.13690691777230923, 0.11673061401456442, 0.8526275802125635, 0.12786124522291376],
         [1, 0.13690691777230923, 0.11673061401456442, 0.8526275802125635, 0.12786124522291376],
         [2, 0.1190375606593736, '-', '-', 0.11117254687976105],
         [3, 0.07213222369517026, '-', '-', 0.06736632518234707],
         [4, 0.09577979975504072, '-', '-', 0.0894514657341721], [5, 0.11005566971626911, '-', '-', 0.1027841047241081],
         [6, 0.20143775924192464, '-', '-', 0.18812842441184086],
         [7, 0.07751195111558946, '-', '-', 0.0723906048763698],
         [8, 0.13698796070154876, '-', '-', 0.12793693350819318],
         [9, 0.09710987898258577, '-', '-', 0.0906936643684433],
         ('Ср. знач', 0.11632885795997908, '-', 0.9339283018229992, 0.10178921539491283)]'''


    #RCReport(p1, p2, Nop, path, {"G0": 12, "gam":3})

import os
from itertools import repeat
from functools import reduce
from io import BytesIO
from pdfrw import PdfReader, PdfWriter, PageMerge
from svglib.svglib import svg2rlg
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.doctemplate import SimpleDocTemplate
from reportlab.platypus.flowables import Spacer, Image
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.tables import TableStyle, Table
from reportlab.graphics.shapes import (Group, Path)
from universal_report.AttrDict import *
from reportlab.lib.pagesizes import A4, landscape
import numpy as np
from matplotlib import pyplot as plt
from svglib.svglib import svg2rlg
import matplotlib
from universal_report.SampleData import UniversalInputDict


def existing(paths):
    for path in paths:
        if os.path.exists(path):
            return path


dataPath = existing([
    "Z:\\Прикладные программы\\Python(data)",
    "D:\\w\\Python(data)",
    "\\\\192.168.0.1\\files\\Прикладные программы\\Python(data)",
])

FONTSIZE = 8
FONTSIZE_HEADING = 10

styles = {
    'default': ParagraphStyle(
        'default',
        fontName='Times',
        fontSize=FONTSIZE,
        leading=12,
        alignment=TA_LEFT,
        valignment='MIDDLE',
    ),
    'default-center': ParagraphStyle(
        'default-center',
        fontName='Times',
        fontSize=FONTSIZE,
        leading=12,
        alignment=TA_CENTER,
        valignment='MIDDLE',
    ),
    'default-right': ParagraphStyle(
        'default-right',
        fontName='Times',
        fontSize=FONTSIZE,
        leading=12,
        alignment=TA_RIGHT,
        valignment='MIDDLE',
    ),
    'heading': ParagraphStyle(
        'heading',
        fontName='TimesDj',
        fontSize=FONTSIZE_HEADING,
        leading=12,
        spaceBefore=10,
        spaceAfter=4,
        alignment=TA_CENTER,
        valignment='MIDDLE',
    )
}

contentPadding = 2  # отступ слева и справа от рамки до контента

printErrorX = 1  # принтер съедает левую границу
printErrorY = 1  # нижняя граница съезжает при печати

margin = AttrDict({
    'top': 5,
    'left': 20 + contentPadding + printErrorX,
    'right': 5 + contentPadding + printErrorX,
    'bottom': 5
})

gray = colors.HexColor(0xebebeb)


def mm_(vs):
    return [v * mm if v is not None else None for v in vs]


def alwaysTrue(*args):
    return True


def alwaysFalse(*args):
    return True


def createFrame(filename, code, date, page, pagesize):
    """ Рендерит рамку и подписи """

    if pagesize is None:
        pagesize = A4

    extra = AttrDict({
        'top': -printErrorY,
        'left': -contentPadding,
        'right': -contentPadding,
        'bottom': 0
    })
    doc = SimpleDocTemplate(filename, pagesize=pagesize, **marginArgs(extra))

    extraStyle = [
        ('SPAN', (0, 0), (-1, 0))
    ]
    tableStyle1 = TableStyleBuilder().grid().italic().alignCenter().build(extraStyle)
    data = adjustedTable([
        [],
        ["Номер документа №:", code, "Дата:", date, "Лист:", page]
    ])

    footerHeight = 5
    # bodyHeight = a4.height - margin.top - margin.bottom - footerHeight - 4

    page_height_mm = pagesize[1] / mm

    bodyHeight = page_height_mm - margin.top - margin.bottom - footerHeight - 4

    colWidths = mm_([37, 65, 19, 28, 18, 18])
    colWidths[1] = '*'

    rowHeights = [bodyHeight * mm, footerHeight * mm]

    table = Table(data, style=tableStyle1, colWidths=colWidths, rowHeights=rowHeights)
    doc.build([table])
    return doc


def marginArgs(extra=None):
    if extra is None:
        extra = AttrDict({
            'top': 0,
            'left': 0,
            'right': 0,
            'bottom': 0
        })
    return {'topMargin': (margin.top + extra.top) * mm,
            'leftMargin': (margin.left + extra.left) * mm,
            'bottomMargin': (margin.bottom + extra.bottom) * mm,
            'rightMargin': (margin.right + extra.right) * mm}


def createFooter(filename, participants, lines, lineHeight, pagesize=None):
    """ Рендерит футер с исполнителями """

    if pagesize is None:
        pagesize = A4

    page_height_mm = pagesize[1] / mm

    top = page_height_mm - margin.top - margin.bottom - lines * lineHeight - 5
    extra = AttrDict({
        'top': top,
        'left': 1,
        'right': 1,
        'bottom': 0
    })
    doc = SimpleDocTemplate(filename, pagesize=pagesize, **marginArgs(extra))
    tableStyle1 = TableStyleBuilder().build()
    data = mapTable(participants, lambda r, c, d: Paragraph(d, styles['default']))
    table = Table(data, style=tableStyle1, colWidths=['57%', '*'])
    doc.build([table])
    return doc


def createHeader(filename, logoPath, accred, pagesize):
    """ Рендерит хедер с логотипом и аккредитацией """

    drawing = svg2rlg(logoPath, True)

    if len(accred) < 2:
        accred = ['', '']

    data = adjustedTable([
        [drawing, 'МОСТДОРГЕОТРЕСТ', 'испытательная лаборатория', ''],
        ['', '', '129344 г. Москва, ул. Искры, д.31, к.1'],
        ['', accred[0]],
        ['', accred[1]],
    ])

    tableStyle = TableStyle([

        ('FONT', (0, 0), (-1, -1), 'Times', 8),

        ('FONT', (1, 0), (1, 0), 'TimesDj', 21),  # МОСТДОРГЕОТРЕСТ
        ('FONT', (2, 0), (2, 0), 'TimesDj', 13),  # испытательная лаборатория
        ('FONT', (1, 2), (-1, -1), 'Times', 8),  # АТТЕСТАТ, РЕЕСТР

        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

        ('TOPPADDING', (0, 0), (-1, -1), 2),

        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),

        # ('GRID', (0,0),(-1,-1),0.1,colors.gray), # отладка
        ('TOPPADDING', (1, 0), (-1, 0), 2.0),  # отступ текста сверху (чтобы линия попала в экватор на глобусе)

        ('BOTTOMPADDING', (2, 0), (2, 0), -5),  # отступ (заступ) снизу от испытательная лаборатория (двигаем адрес)

        ('BOTTOMPADDING', (1, 2), (-1, 2), -2),  # отступ (заступ) снизу от АТТЕСТАТ и РЕЕСТР

        # ('LEFTPADDING', (0, 0), (0, 0), 5),
        # ('RIGHTPADDING', (0, 0), (0, 0), 5),

        # ('RIGHTPADDING', (0,0), (0,0), 3 * mm),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),

        ('LINEBELOW', (1, 1), (2, 1), 1, colors.black),
        ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (1, 2), (2, 2)),
        ('SPAN', (1, 3), (2, 3)),
        ('SPAN', (0, 0), (0, 3)),
        # ('SPAN', (3,0), (3,1))
    ])

    table = Table(data, style=tableStyle, colWidths=[2.3 * cm, 8.4 * cm, 6.1 * cm, '*'])

    extra = AttrDict({
        'left': 0,
        'top': 0,
        'right': 0,
        'bottom': 0
    })

    doc = SimpleDocTemplate(filename, pagesize=pagesize, **marginArgs(extra))

    doc.build([table])

    return doc


def mergeFirstPage(filename, *inputs):
    """ Объединяет (оверлеет) несколько одностраничных pdf в один """
    for inp in inputs:
        if isinstance(inp, BytesIO):
            inp.seek(0)
    readers = [PdfReader(inp) for inp in inputs]
    merger = PageMerge(readers[0].pages[0])
    for reader in readers[1:]:
        merger.add(reader.pages[0])
    merger.render()
    writer = PdfWriter()
    writer.write(filename, readers[0])


def appendPages(filename, *inputs):
    """ Объединяет (апендит) несколько одностраничных pdf в один многостраничный """
    for inp in inputs:
        if isinstance(inp, BytesIO):
            inp.seek(0)
    writer = PdfWriter()
    readers = [PdfReader(inp) for inp in inputs]
    for reader in readers:
        for page in reader.pages:
            writer.addpage(page)
    writer.write(filename)


def ruWithPrec(val, prec, none='-'):
    """ Возвращает значение `val` в виде строки с `prec` знаков после запятой
    используя запятую как разделитель дробной части
    """
    if isinstance(val, str):
        return val
    if val is None:
        return none
    fmt = "{:." + str(int(prec)) + "f}"
    return fmt.format(val).replace(".", ",")


def reportProbeTable2(probe_data, probe_data_prec):
    """ Таблица характеристик грунта """
    d = probe_data
    p = probe_data_prec

    data = [
        ['T, °C', d.t, 1],
        ['ρ<sub rise="2.5" size="6">s</sub>, г/см<sup rise="2.5" size="5">3</sup>', d.rhos, p.rhos],
        ['ρ, г/см<sup rise="2.5" size="5">3</sup>', d.rho, p.rho],
        ['ρ<sub rise="2.5" size="6">d</sub>, г/см<sup rise="2.5" size="5">3</sup>', d.rhod, p.rhod],
        ['n, %', d.n, p.n],
        ['e, ед.', d.e, p.e],
        ['W<sub rise="0.5" size="6">tot</sub>, %', d.wtot, p.wtot],
        ['W<sub rise="0.5" size="6">m</sub>, %', d.wm, p.wm],
        ['W<sub rise="0.5" size="6">w</sub>, %', d.ww, p.ww],
        ['I<sub rise="0.5" size="6">tot</sub>, д.е', d.itot, p.itot],
        ['I<sub rise="0.5" size="6">i</sub>, д.е', d.ii, p.ii],
        ['S<sub rise="0.5" size="6">r</sub>, д.е.', d.sr, p.sr],
        ['I<sub rise="0.5" size="5">P</sub>, %', d.ip, p.ip],
        ['I<sub rise="0.5" size="5">L</sub>, д.е.', d.il, p.il],
        ['I<sub rise="0.5" size="6">r</sub>, %', d.ir, p.ir],
        ['D<sub rise="0.5" size="6">sal</sub>, %', d.dsal, p.dsal],
    ]

    data = [[row[0], ruWithPrec(row[1], row[2])] for row in data]

    # переформатируем [16][2] в [8][4] и транспонируем в [4][8]
    count = int(len(data) / 2)
    table = transpose([flatten1(e) for e in zip(data[:count], data[count:])])

    return table


def transparentBackground(path: Path):
    if path.fillColor == colors.white:
        path.fillColor = None


def thinBorders(path: Path):
    l = len(path.points)
    if l == 4 or l == 8:
        if path.strokeWidth > 0.6:
            path.strokeWidth = 0.6


def fixDrawing(drawing, mutatePath):
    contents = list(drawing.contents)
    i = 0
    while len(contents) > i:
        item = contents[i]
        if isinstance(item, Group):
            contents += list(item.contents)
        elif isinstance(item, Path):
            mutatePath(item)
        i += 1


def reportProbeTable3(probe_data, probe_data_prec):
    """ Таблица характеристик грунта """
    d = probe_data
    p = probe_data_prec

    data = [
        ['ρ<sub rise="2.5" size="6">s</sub>, г/см<sup rise="2.5" size="5">3</sup>', d.rhos, p.rhos],
        ['ρ, г/см<sup rise="2.5" size="5">3</sup>', d.rho, p.rho],
        ['ρ<sub rise="2.5" size="6">d</sub>, г/см<sup rise="2.5" size="5">3</sup>', d.rhod, p.rhod],
        ['n, %', d.n, p.n],
        ['e, ед.', d.e, p.e],
        ['W, %', d.w, p.w],
        ['S<sub rise="0.5" size="6">r</sub>, д.е.', d.sr, p.sr],
        ['I<sub rise="0.5" size="5">P</sub>, %', d.ip, p.ip],
        ['I<sub rise="0.5" size="5">L</sub>, д.е.', d.il, p.il],
        ['I<sub rise="0.5" size="6">om</sub>, %', d.iom, p.iom]
    ]

    data = [[row[0], ruWithPrec(row[1], row[2])] for row in data]

    return transpose(data)


def flatten1(vs):
    """ Распаковывает лист листов (или кортежей) на 1 в глубину.
```
>>> flatten1([(3,4),(5,6)])
[3, 4, 5, 6]

```
"""
    return list(reduce(lambda p, c: p + c, vs))


def toList(vs):
    if isinstance(vs, list):
        return vs
    return [vs]


def init_fonts():
    fonts = {
        'Times': 'Times.ttf',
        'TimesBold': 'TimesDj.ttf',
        'TimesK': 'TimesK.ttf'
    }
    for fontName, fontFile in fonts.items():
        pdfmetrics.registerFont(TTFont(fontName, os.path.join(dataPath, fontFile)))


def needParagraph(d):
    return isinstance(d, str) and (d.find('<sup') > -1 or d.find('<sub') > -1)


class Cell:
    """ Тип-контейнер для объединённых ячеек и ячеек с backgroundом """

    def __init__(self, data, rowSpan=1, colSpan=1, background=None):
        self._data = data
        self._rowSpan = rowSpan
        self._colSpan = colSpan
        self._background = background

    def data(self):
        return self._data

    def rowSpan(self):
        return self._rowSpan

    def colSpan(self):
        return self._colSpan

    def background(self):
        return self._background


class RTable:
    """ Помошник для создания таблиц (вычисляет спаны (спанит ячейки содержащие None с ячейками слева) и стили)"""

    def __init__(self):
        self._table = None
        self._paragraph = None
        self._style = None
        self._align = TA_LEFT

    def table(self, table):
        """ Задаёт таблицу с данными, в ячейках могут быть строки, `None`
        или объекты типа `Cell` (объединенные ячейки или ячейки с backgroundом)
        """
        self._table = table
        return self

    def c(self, data, rowSpan=1, colSpan=1, background=None):
        return Cell(data, rowSpan, colSpan, background)

    def cg(self, data):
        """ Возвращает ячейку с серым backgroundом """
        return Cell(data, 1, 1, gray)

    def c2g(self, data):
        """ Возвращает ячейку растянутую на две колонки с серым backgroundом """
        return Cell(data, 1, 2, gray)

    def c3g(self, data):
        """ Возвращает ячейку растянутую на три колонки с серым backgroundом """
        return Cell(data, 1, 3, gray)

    def paragraph(self, paragraph):
        """ Задаёт функцию paragraph(row, column, data) -> Bool
        которая определяет нужно ли заворачивать ячейку в Pargagraph """
        self._paragraph = paragraph
        return self

    def style(self, style):
        """ Задаёт стиль """
        self._style = style
        return self

    def alignLeft(self):
        """ Задаёт выравнивание по левому краю """
        self._align = TA_LEFT
        return self

    def alignRight(self):
        """ Задаёт выравнивание по правому краю """
        self._align = TA_RIGHT
        return self

    def alignCenter(self):
        """ Задаёт выравнивание по центру """
        self._align = TA_CENTER
        return self

    def build(self):
        """ Вычисляет спаны стили и заворачивает ячейки удовлетворяющие условию в параграфы.

Возвращает кортеж (`table`, `spans`, `background`)

`table` - выровненная таблица данных для конструктора `Table`

`spans`, `background` - стили для конструктора `TableStyle` (или `TableStyleBuiler`)

```
>>> r = RTable()

>>> r.table([['1','2'],['3']]).build()
([['1', '2'], ['3', None]], [('SPAN', (0, 1), (1, 1))], [])

>>> r.table([[r.cg('1'),'2'],['3']]).build()
([['1', '2'], ['3', None]], [('SPAN', (0, 1), (1, 1))], [('BACKGROUND', (0, 0), (0, 0), Color(.921569,.921569,.921569,1))])

>>> r.table([[r.c2g('1'),'2'],['3']]).build()
([['1', None, '2'], ['3', None, None]], [('SPAN', (0, 0), (1, 0)), ('SPAN', (0, 1), (2, 1))], [('BACKGROUND', (0, 0), (1, 0), Color(.921569,.921569,.921569,1))])

>>> r.paragraph(lambda row,column,data: row > 0).table([['1','2'],['3']]).build()
([['1', '2'], [Paragraph('3', styles['default']), None]], [('SPAN', (0, 1), (1, 1))], [])

>>> r.paragraph(lambda row,column,data: row > 0).alignCenter().table([['1','2'],['3']]).build()
([['1', '2'], [Paragraph('3', styles['default-center']), None]], [('SPAN', (0, 1), (1, 1))], [])

```
"""
        style = self._style
        paragraph = self._paragraph

        if style is None:
            style = styles[{TA_LEFT: 'default', TA_CENTER: 'default-center', TA_RIGHT: 'default-right'}[self._align]]

        if paragraph is None:
            paragraph = lambda r, c, d: needParagraph(d)

        def wrap(r, c, d):
            if d is None:
                return d
            if isinstance(d, int) or isinstance(d, float):
                d = str(d)
            return Paragraph(d, style) if paragraph(r, c, d) else d

        background = []
        spans = []
        table = []

        for r, row in enumerate(self._table):
            shift = 0
            row_ = []
            for c, cell in enumerate(row):
                if isinstance(cell, Cell):
                    row_.append(wrap(r, c + shift, cell.data()))
                    noneCells = cell.colSpan() - 1
                    row_ = row_ + list(repeat(None, noneCells))
                    if cell.background():
                        background.append(("BACKGROUND", (c + shift, r), (c + shift + noneCells, r), cell.background()))
                    shift += noneCells
                else:
                    row_.append(wrap(r, c + shift, cell))
            table.append(row_)

        def spanRanges(row):
            res = []
            p = -1
            for c, cell in enumerate(row):
                if cell is None:
                    if p > -1:
                        pass
                    else:
                        p = c - 1
                else:
                    if p > -1:
                        res.append([p, c - 1])
                    p = -1
            if p > -1:
                res.append([p, len(row) - 1])
            return res

        table = adjustedTable(table, None)
        for r, row in enumerate(table):
            ranges = spanRanges(row)
            for range_ in ranges:
                spans.append(('SPAN', (range_[0], r), (range_[1], r)))

        return table, spans, background


class TableStyleBuilder:
    """ Помошник для стилей таблиц """

    def __init__(self):
        self._grid = False
        self._align = TA_LEFT
        self._topPadding = 0
        self._bottomPadding = 0
        self._verticalAlign = 'MIDDLE'
        self._italic = False
        self._bold = False

    def verticalPadding(self, value):
        self._topPadding = value
        self._bottomPadding = value
        return self

    def alignLeft(self):
        self._align = TA_LEFT
        return self

    def alignCenter(self):
        self._align = TA_CENTER
        return self

    def grid(self, grid=True):
        self._grid = grid
        return self

    def italic(self, italic=True):
        self._italic = italic
        return self

    def bold(self, bold=True):
        self._bold = bold
        return self

    def build(self, *extra):

        font = 'Times'
        if self._italic:
            font = 'TimesK'
        if self._bold:
            font = 'TimesDj'

        ops = [
            ('FONT', (0, 0), (-1, -1), font, 8),
            ('VALIGN', (0, 0), (-1, -1), self._verticalAlign),
            ('TOPPADDING', (0, 0), (-1, -1), self._topPadding),
            ('BOTTOMPADDING', (0, 0), (-1, -1), self._bottomPadding)
        ]

        if self._grid:
            ops.append(('GRID', (0, 0), (-1, -1), 0.8, colors.black))

        ops.append(('ALIGN', (0, 0), (-1, -1), {TA_LEFT: 'LEFT', TA_CENTER: 'CENTER', TA_RIGHT: 'RIGHT'}[self._align]))

        for item in extra:
            ops += item
        return TableStyle(ops)


def transpose(table):
    """ Транспонирует таблицу """
    return list(map(list, zip(*table)))


def columnCount(table):
    return max([len(row) for row in table])


def adjusted(vs, size, v=None):
    """ Добавляет `v` в конец листа пока длинна не станет `size` """
    return list(vs) + list(repeat(v, size - len(vs)))


def adjustedTable(table, v=None):
    """ Выравнивает число колонок в таблице прибавляя к каждой строке нужное число `v` """
    size = columnCount(table)
    return [adjusted(row, size, v) for row in table]


def mapTable(table, setter):
    """ Преобразует таблицу функцией `setter(row,column,data)` обходя её по всем строкам и столбцам
```
>>> mapTable([[1,2],[3,4]], lambda r,c,d: d+1)
[[2, 3], [4, 5]]

>>> mapTable([[1,2],[3,4]], lambda r,c,d: d+2 if r > 0 else d+1)
[[2, 3], [5, 6]]

>>> mapTable([[1,2],[3,4]], lambda r,c,d: ''.join(repeat(str(d),d)))
[['1', '22'], ['333', '4444']]
```
    """
    table_ = []
    for r, row in enumerate(table):
        row_ = []
        for c, cell in enumerate(row):
            row_.append(setter(r, c, cell))
        table_.append(row_)
    return table_


class Report:
    """ Базовый класс протокола испытания.
    Для создания шаблона конкретного испытания нужно наследовать этот класс
    и переопределить методы `title()`, `content()` и `examTable()`
    """

    def __init__(self, path, pages, pagesize=None):
        """ `path` - путь для сохранения файла
        `pages` - количество страниц в протоколе
        """
        if pagesize is None:
            pagesize = A4
        self._pagesize = pagesize
        self._path = path
        self._pages = pages

    def probeTable1(self, object_data, probe_data, exam_data):
        r = RTable()
        """
        r.table([
            [r.cg('Заказчик'), object_data.customerName],
            [r.cg('Объект'), object_data.objectName],
            [r.c2g('Наименование выработки'), probe_data.well, r.cg('Глубина отбора'), ruWithPrec(probe_data.depth, 1)],
            [r.c2g('Лабораторный номер'), probe_data.labNumber, r.cg('ИГЭ/РГЭ'), ruWithPrec(probe_data.ege, 0),],
            [r.c2g('Наименование грунта'), probe_data.classification],
            [r.c2g('Протокол испытаний №'), exam_data.report_number],
        ])
        """
        r.table([
            [r.c2g('Протокол испытаний №'), exam_data.report_number],
            [r.cg('Заказчик'), object_data.customerName],
            [r.cg('Объект'), object_data.objectName],
            [r.c3g('Привязка пробы (скв.; глубина отбора)'), probe_data.well + "; " + ruWithPrec(probe_data.depth, 1),
             r.cg("ИГЭ/РГЭ:"), ruWithPrec(probe_data.ege, 0)],
            [r.c3g('Лабораторный номер'), probe_data.lab_no],
            [r.c2g('Наименование грунта'), probe_data.classification]
        ])
        table, spans, background = r.alignLeft().paragraph(alwaysTrue).build()

        tableStyle = TableStyleBuilder().grid().alignLeft().build(spans, background)

        w = 17.5 * mm

        return Table(table, style=tableStyle, colWidths=[w, w, w, 3 * w, w, '*'])
        # , colWidths=[20 * mm, 20 * mm, '*', 40 * mm, '*']

    def probeTable2(self, object_data, probe_data, exam_data):
        probe_data_prec = AttrDict({
            't': 1,
            'rhos': 2,
            'rho': 2,
            'rhod': 2,
            'n': 1,
            'e': 2,
            'wtot': 1,
            'wm': 1,
            'ww': 1,
            'itot': 2,
            'ii': 2,
            'sr': 2,
            'ip': 1,
            'il': 2,
            'ir': 1,
            'dsal': 3
        })

        table = reportProbeTable2(probe_data, probe_data_prec)

        r = RTable()

        table = mapTable(table, lambda row, c, d: d if row % 2 else r.cg(d))

        r.table(table)

        table, spans, background = r.paragraph(alwaysTrue).alignCenter().build()

        tableStyle = TableStyleBuilder().grid().alignCenter().build(spans, background)

        return Table(table, style=tableStyle)

    def content(self, number, object_data, probe_data, exam_data):
        """ Блок "РЕЗУЛЬТАТЫ ИСПЫТАНИЯ". Должен возвращать один или несколько `reportlab.platypus.flowables.Flowable`.

        `number` - номер страницы (0-based)

        Нужно переопределить в наследуемом классе.
        """
        return self.paragraph('Метод Report.content() (РЕЗУЛЬТАТЫ ИСПЫТАНИЯ) нужно переопределить в наследуемом классе')

    def title(self):
        """ Заголовок страницы (название испытания). Должен возвращать один или несколько `reportlab.platypus.flowables.Flowable`.

        Нужно переопределить в наследуемом классе.
        """
        return self.heading(
            'Метод Report.title() (Заголовок страницы (название испытания)) нужно переопределить в наследуемом классе')

    def examTable(self, object_data, probe_data, exam_data):
        """ Блок "СВЕДЕНИЯ ОБ ИСПЫТАНИИ". Должен возвращать один или несколько `reportlab.platypus.flowables.Flowable`.

        Нужно переопределить в наследуемом классе.
        """
        return self.paragraph(
            'Метод Report.examTable() (СВЕДЕНИЯ ОБ ИСПЫТАНИИ) нужно переопределить в наследуемом классе')

    def heading(self, text):
        return Paragraph(text, styles['heading'])

    def paragraph(self, text):
        return Paragraph(text, styles['default'])

    def page(self, number, object_data, probe_data, exam_data):

        bytes_ = BytesIO()

        headerHeightAndMagrin = 24

        participants = object_data.participants
        footerLines = len(participants) + 1
        footerLineHeight = 6

        extra = AttrDict({
            'top': headerHeightAndMagrin,
            'left': 0,
            'right': 0,
            'bottom': footerLineHeight * footerLines
        })

        doc = SimpleDocTemplate(bytes_, pagesize=self._pagesize, **marginArgs(extra))

        flowables = [
            *toList(self.title()),
            *toList(self.probeTable1(object_data, probe_data, exam_data)),
            self.heading('ХАРАКТЕРИСТИКИ ГРУНТА'),
            *toList(self.probeTable2(object_data, probe_data, exam_data)),
            self.heading('СВЕДЕНИЯ ОБ ИСПЫТАНИИ'),
            *toList(self.examTable(object_data, probe_data, exam_data)),
            self.heading('РЕЗУЛЬТАТЫ ИСПЫТАНИЯ'),
            *toList(self.content(number, object_data, probe_data, exam_data))
        ]

        doc.build(flowables)

        return bytes_

    def build(self, object_data, probe_data, exam_data):

        pages = []

        for page in range(self._pages):
            frameLayer = BytesIO()
            headerLayer = BytesIO()
            footerLayer = BytesIO()
            mergedLayers = BytesIO()

            createFrame(frameLayer, exam_data.code, exam_data.date, '{}/{}'.format(page + 1, self._pages),
                        self._pagesize)

            logoPath = os.path.join(dataPath, 'logo_small.svg')

            createHeader(headerLayer, logoPath, object_data.accred, self._pagesize)

            participants = object_data.participants

            footerLines = len(participants) + 1
            footerLineHeight = 6

            createFooter(footerLayer, participants, footerLines, footerLineHeight, self._pagesize)

            contentLayer = self.page(page, object_data, probe_data, exam_data)

            mergeFirstPage(mergedLayers, frameLayer, headerLayer, footerLayer, contentLayer)

            pages.append(mergedLayers)

        appendPages(self._path, *pages)


class UniversalReport(Report):
    """
        Класс универсального построителя отчета.
        В качестве входного массива данных исполдьзует класс UniversalInputDict.
        Реализует полное сохранение объекта в один
    """

    def __init__(self, path, data: 'UniversalInputDict'):
        self.current_page = 0
        '''текущая генерируемая страница'''

        self.pages = []
        '''список всех генерируемых страниц'''

        super().__init__(path, len(data.lists))

        self._test_heading = data.test_heading
        '''название отчета для self.title()'''

        self._lists = data.lists
        '''список всех страниц из UniversalInputDict'''

        self._object_data = data.object_data

        self.build_all()

    def build_all(self):
        """
        Построитель всего объекта. Проходит по страницам в `UniversalInputDict.lists`
        """
        for page in range(len(self._lists)):
            probe_data = self._lists[page].probe_data
            exam_data = self._lists[page].exam_data

            self.current_page = page
            self.build(self._object_data, probe_data, exam_data)

        appendPages(self._path, *self.pages)

    def build(self, object_data, probe_data, exam_data):
        """
        Вариант билда родителя для одной страницы.
         Должен запускаться только из build_all
        """
        frameLayer = BytesIO()
        headerLayer = BytesIO()
        footerLayer = BytesIO()
        mergedLayers = BytesIO()

        createFrame(frameLayer, probe_data.code, probe_data.date, '{}/{}'.format(self.current_page + 1, self._pages),
                    self._pagesize)

        logoPath = os.path.join(dataPath, 'logo_small.svg')

        createHeader(headerLayer, logoPath, object_data.accred, self._pagesize)

        participants = object_data.participants

        footerLines = len(participants) + 1
        footerLineHeight = 6

        createFooter(footerLayer, participants, footerLines, footerLineHeight, self._pagesize)

        contentLayer = self.page(self.current_page, object_data, probe_data, exam_data)

        mergeFirstPage(mergedLayers, frameLayer, headerLayer, footerLayer, contentLayer)

        self.pages.append(mergedLayers)

    def title(self):
        return self.heading(self._test_heading)

    def examTable(self, object_data, probe_data, exam_data):
        r = RTable()

        exam_table = []
        for item in exam_data:
            row = []
            for key in item:
                if not item[key]:
                    row.append(r.cg(key))
                    continue

                row.append(r.cg(key))
                row.append(item[key])

            exam_table.append(row)

        r.table(exam_table)

        table, spans, background = r.paragraph(alwaysTrue).build()
        tableStyle = TableStyleBuilder().grid().alignLeft().build(spans, background)
        return Table(table, style=tableStyle, colWidths=[40 * mm, '*', '*', '*', '*', '*', '*'])

    def content(self, number, object_data, probe_data, exam_data):

        results_table = probe_data['results_table']

        for i in range(len(results_table) - 1):
            # Весь ИФ для тестов
            if type(results_table[i]) == str:
                if results_table[i] == 'sample_drawing':
                    xs = np.linspace(0, 2 * np.pi)
                    ys = np.sin(xs)
                    xs, ys = [xs, ys]
                    drawing_long = points_to_drawing(xs, ys, 120 * mm, 40 * mm, xlabel="Ось X", ylabel="Ось Y")
                    results_table[i] = drawing_long

                if results_table[i] == 'sample_table':
                    pass

                continue

            # Обход случая, когда данные подабтся списком в паре
            if type(results_table[i]) == list:
                for j in range(len(results_table[i])):
                    # Весь ИФ для тестов
                    if type(results_table[i][j]) == str:
                        if results_table[i][j] == 'sample_drawing':
                            xs = np.linspace(0, 2 * np.pi)
                            ys = np.sin(xs)
                            xs, ys = [xs, ys]
                            drawing = points_to_drawing(xs, ys, 60 * mm, 40 * mm, xlabel="Ось X", ylabel="Ось Y")
                            results_table[i][j] = drawing

                        if results_table[i][j] == 'sample_table':
                            _sample_table = {'title': 'Напряжение, МПа',
                                             'data_cols': [['sigma_3', 0.1, 0.2, 0.3],
                                                           ['sigma_1c', 0.1, 0.2, 0.3],
                                                           ['sigma_1f', 0.355, 0.765, 1.080]]}

                            _result_table = self.reportProbeTable3(_sample_table)
                            results_table[i][j] = _result_table

                results_table[i] = Table([results_table[i]], style=[('VALIGN', (0, 0), (-1, -1), 'CENTER')])
                continue

        # Форматирование конечной таблицы с результатами
        if type(results_table[-1]) == dict:
            r = RTable()
            exam_table = []
            for key in results_table[-1]:
                if not results_table[-1][key]:
                    exam_table.append([r.cg(key), '-'])
                    continue
                exam_table.append([r.cg(key), results_table[-1][key]])

            r.table(exam_table)
            table, spans, background = r.paragraph(alwaysTrue).build()
            tableStyle = TableStyleBuilder().grid().alignLeft().build(spans, background)
            resltTable = Table(table, style=tableStyle, colWidths=['*', '*', '*', '*', '*', '*', '*'])
            results_table[-1] = resltTable

        result = results_table

        return result

    def probeTable1(self, object_data, probe_data, exam_data):
        r = RTable()
        r.table([
            [r.c2g('Протокол испытаний №'), probe_data.report_number],
            [r.cg('Заказчик'), object_data.customerName],
            [r.cg('Объект'), object_data.objectName],
            [r.c3g('Привязка пробы (скв.; глубина отбора)'), probe_data.well + "; " + ruWithPrec(probe_data.depth, 1),
             r.cg("ИГЭ/РГЭ:"), ruWithPrec(probe_data.ege, 0)],
            [r.c3g('Лабораторный номер'), probe_data.lab_no],
            [r.c2g('Наименование грунта'), probe_data.classification]
        ])
        table, spans, background = r.alignLeft().paragraph(alwaysTrue).build()

        tableStyle = TableStyleBuilder().grid().alignLeft().build(spans, background)

        w = 17.5 * mm

        return Table(table, style=tableStyle, colWidths=[w, w, w, 3 * w, w, '*'])

    def probeTable2(self, object_data, probe_data, exam_data):
        _probe_data = probe_data.physical_properties_table

        table = self.reportProbeTable2(_probe_data)

        if len(table) < 1:
            Spacer(cm, cm)

        r = RTable()

        table = mapTable(table, lambda row, c, d: d if row % 2 else r.cg(d))

        r.table(table)

        table, spans, background = r.paragraph(alwaysTrue).alignCenter().build()

        tableStyle = TableStyleBuilder().grid().alignCenter().build(spans, background)

        return Table(table, style=tableStyle)

    @staticmethod
    def reportProbeTable2(probe_data):
        """ Таблица характеристик грунта.
        Печатает таблицу в одну (до 9 элементов включительно) и
        в две строчки (до 18 элементов включительно).

        !Нужно доработать для произвольного числа строк!
        """
        d = probe_data
        data = []

        for key in d:
            if d[key]:
                data.append([key, d[key]])
                continue
            data.append(['', ''])

        while len(data) % 10 != 0:
            data.append(['', ''])

        rows = int(len(data) / 10)
        if rows > 1:
            # Произвольное число строк делать здесь!

            # переформатируем [16][2] в [8][4] и транспонируем в [4][8]
            count = int(len(data) / rows)
            table = transpose([flatten1(e) for e in zip(data[:count], data[count:])])
            return table

        table = transpose(data)
        return table

    @staticmethod
    def reportProbeTable3(data: 'dict') -> 'Table':
        table = data['data_cols']
        table = adjustedTable(table)
        table = transpose(table)
        table = mapTable(table, lambda r, c, d: ruWithPrec(d, 2 if c == 0 else 3, ""))
        header = [data['title']]
        table = [header] + table

        r = RTable()
        table = mapTable(table, UniversalReport.grayRows(2))
        r.table(table)
        table, spans, background = r.paragraph(alwaysTrue).alignCenter().build()
        tableStyle = TableStyleBuilder().grid().alignCenter().build(spans, background)
        return Table(table, style=tableStyle)

    @staticmethod
    def grayRows(n):
        return lambda r, c, d: Cell(d, 1, 1, gray) if r < n else d

def test_UniversalReport():
    """ Функция для тестирования UniversalReport"""
    inputData = UniversalInputDict()
    inputData.set_data()

    # init_fonts()

    path = os.path.join(existing([
        "C:/Users/Пользователь/Desktop/Новая папка (2)/Новая папка (2)",
        "D:\\w"
    ]), "test_UniversalReport.pdf")

    UniversalReport(path, inputData)


def points_to_drawing(xs, ys, width=None, height=None, xlabel=None, ylabel=None):
    svg = BytesIO()

    font_size = 7

    font = {'family': 'Times New Roman', 'size': font_size}

    matplotlib.rc('font', **font)
    matplotlib.rc('lines', linewidth=1)
    matplotlib.rc('axes', titlesize=font_size + 1, labelsize=font_size)  # размер названия и подписей
    matplotlib.rc('xtick', labelsize=font_size)
    matplotlib.rc('ytick', labelsize=font_size)
    matplotlib.rc('ytick.major', size=1)
    matplotlib.rc('ytick.minor', size=1)
    matplotlib.rc('xtick.major', size=1)
    matplotlib.rc('xtick.minor', size=1)

    # matplotlib.rc('figure', frameon=False)
    # matplotlib.rc('patch', linewidth=0, edgecolor='white')
    # plt.figure()

    fig, ax = plt.subplots(1, 1, tight_layout=True)

    if width is None:
        width = 150 * mm
    if height is None:
        height = 100 * mm

    fig.set_size_inches(width / 25 / mm, height / 25 / mm)

    plt.plot(xs, ys)
    ax.grid(True)

    if xlabel is not None:
        ax.set_xlabel(xlabel)

    if ylabel is not None:
        ax.set_ylabel(ylabel)

    plt.tight_layout()

    plt.savefig(svg, format='svg')

    svg.seek(0)

    drawing = svg2rlg(svg, True)

    drawing.hAlign = 'CENTER'

    return drawing


if __name__ == "__main__":
    test_UniversalReport()

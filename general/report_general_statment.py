import math
import os
import sys
from itertools import repeat
from functools import reduce
from io import BytesIO
from textwrap import wrap

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
from reportlab.lib.pagesizes import A4, landscape

from excel_statment.params import accreditation


class AttrDict:
    """ Класс преобразующий словарь в объект с набором атрибутов
    в котором имена атрибутов соответствуют ключам словаря а значения значениям.

Проще говоря чтобы вместо foo['bar'] использовать foo.bar

```
>>> a = AttrDict({'b': 1,'c':2})
>>> a.b
1
>>> a.c
2
>>> a.d = 3
>>> a.d
3
>>> a['b']
1
```
"""

    def __init__(self, data):
        for n, v in data.items():
            self.__setattr__(n, v)

    def __getitem__(self, key):
        return self.__getattribute__(key)


def existing(paths):
    for path in paths:
        if os.path.exists(path):
            return path


dataPath = existing([
    "Z:\\Прикладные программы\\Python(data)",
    "D:\\w\\Python(data)",
    "\\\\192.168.0.1\\files\\Прикладные программы\\Python(data)",
])

styles = {
    'default': ParagraphStyle(
        'default',
        fontName='Times',
        fontSize=8,
        leading=12,
        alignment=TA_LEFT,
        valignment='MIDDLE',
    ),
    'default-center': ParagraphStyle(
        'default-center',
        fontName='Times',
        fontSize=8,
        leading=12,
        alignment=TA_CENTER,
        valignment='MIDDLE',
    ),
    'default-right': ParagraphStyle(
        'default-right',
        fontName='Times',
        fontSize=8,
        leading=12,
        alignment=TA_RIGHT,
        valignment='MIDDLE',
    ),
    'heading': ParagraphStyle(
        'heading',
        fontName='TimesBold',
        fontSize=10,
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

    from textwrap import wrap
    if type_format == 0:
        data = adjustedTable([
            [drawing, '  МОСТДОРГЕОТРЕСТ  ', '  испытательная лаборатория  ', '', customer_data_info[0],
             customer_data_zakazchik[0]],
            ['', '', '  129344 г. Москва, ул. Искры, д.31, к.1', '', '', customer_data_zakazchik[1]],
            ['', accred[0], '', '', customer_data_info[1], customer_data_object[0]],
            ['', accred[1], '', '', '', customer_data_object[1]],
        ])
        tableStyle = TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Times', 8),
            ('FONT', (1, 0), (1, 0), 'TimesBold', 21),  # МОСТДОРГЕОТРЕСТ
            ('FONT', (2, 0), (2, 0), 'TimesBold', 13),  # испытательная лаборатория
            ('FONT', (1, 2), (-1, -1), 'Times', 8),  # АТТЕСТАТ, РЕЕСТР

            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

            ('BACKGROUND', (4, 0), (4, 3), gray),

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
            ('ALIGN', (0, 0), (0, 5), 'LEFT'),

            ('LEFTPADDING', (4, 0), (5, 5), 18),

            ('BOX', (4, 0), (5, 5), 1, colors.black),
            ('LINEBELOW', (1, 1), (2, 1), 0, colors.black),

            ('LINEBELOW', (4, 1), (5, 1), 0, colors.black),
            ('GRID', (5, 0), (4, 3), .3, colors.black),
            ('SPAN', (1, 0), (1, 1)),
            ('SPAN', (1, 2), (2, 2)),
            ('SPAN', (1, 3), (2, 3)),
            ('SPAN', (0, 0), (0, 3)),
            # ('SPAN', (3,0), (3,1))
        ])
    else:
        data = adjustedTable([
            [drawing, 'МОСТДОРГЕОТРЕСТ', 'испытательная лаборатория', '', '',
             ''],
            ['', '', '129344 г. Москва, ул. Искры, д.31, к.1', '', ''],
            ['', accred[0]],
            ['', accred[1]],
        ])
        tableStyle = TableStyle([

            ('FONT', (0, 0), (-1, -1), 'Times', 8),

            ('FONT', (1, 0), (1, 0), 'TimesBold', 21),  # МОСТДОРГЕОТРЕСТ
            ('FONT', (2, 0), (2, 0), 'TimesBold', 13),  # испытательная лаборатория
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


def initFonts():
    fonts = {
        'Times': 'Times.ttf',
        'TimesBold': 'TimesDj.ttf',
        'TimesItalic': 'TimesK.ttf'
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
            font = 'TimesItalic'
        if self._bold:
            font = 'TimesBold'

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

        self._pages = len(pod_mass)  # TODO 'pages' количество страниц

    def probeTable1(self, examData):

        r = RTable()
        r.table([
            [r.cg('Заказчик'), customer_data[0]],
            [r.cg('Объект'), customer_data[1]],
        ])
        table, spans, background = r.alignLeft().paragraph(alwaysTrue).build()

        tableStyle = TableStyleBuilder().grid().alignLeft().build(spans, background)

        return Table(table, style=tableStyle, colWidths=[20 * mm, 230 * mm])

        r = RTable()

        table = mapTable(table, lambda row, c, d: d if row % 2 else r.cg(d))

        r.table(table)

        table, spans, background = r.paragraph(alwaysTrue).alignCenter().build()

        tableStyle = TableStyleBuilder().grid().alignCenter().build(spans, background)

        return Table(table, style=tableStyle)

    def content(self, number, objectData, examData):
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

    def examTable(self, objectData, examData):
        """ Блок "СВЕДЕНИЯ ОБ ИСПЫТАНИИ". Должен возвращать один или несколько `reportlab.platypus.flowables.Flowable`.

        Нужно переопределить в наследуемом классе.
        """
        return self.paragraph(
            'Метод Report.examTable() (СВЕДЕНИЯ ОБ ИСПЫТАНИИ) нужно переопределить в наследуемом классе')

    def heading(self, text):
        return Paragraph(text, styles['heading'])

    def paragraph(self, text):
        return Paragraph(text, styles['default'])

    def page(self, number, objectData, examData):

        bytes_ = BytesIO()

        headerHeightAndMagrin = 24

        participants = objectData.participants
        footerLines = len(participants) + 1
        footerLineHeight = 6

        extra = AttrDict({
            'top': headerHeightAndMagrin,
            'left': 0,
            'right': 0,
            'bottom': footerLineHeight * footerLines
        })

        doc = SimpleDocTemplate(bytes_, pagesize=self._pagesize, **marginArgs(extra))
        if type_format == 0:

            flowables = [
                # *toList(self.probeTable1(objectData, probeData, examData)),
                *toList(self.title()),
                # *toList(self.probeTable1(objectData, probeData, examData)),
                # self.heading('ХАРАКТЕРИСТИКИ ГРУНТА'),
                # *toList(self.probeTable2(objectData, probeData, examData)),
                # self.heading('СВЕДЕНИЯ ОБ ИСПЫТАНИИ'),
                # *toList(self.examTable(objectData, probeData, examData)),
                # self.heading('РЕЗУЛЬТАТЫ ИСПЫТАНИЯ'),
                *toList(self.content(number, objectData, examData))
            ]
        else:
            flowables = [
                *toList(self.probeTable1(examData)),
                *toList(self.title()),
                # *toList(self.probeTable1(objectData, probeData, examData)),
                # self.heading('ХАРАКТЕРИСТИКИ ГРУНТА'),
                # *toList(self.probeTable2(objectData, probeData, examData)),
                # self.heading('СВЕДЕНИЯ ОБ ИСПЫТАНИИ'),
                # *toList(self.examTable(objectData, probeData, examData)),
                # self.heading('РЕЗУЛЬТАТЫ ИСПЫТАНИЯ'),
                *toList(self.content(number, objectData, examData))
            ]

        doc.build(flowables)

        return bytes_

    def build(self, objectData, examData):

        pages = []

        for page in range(self._pages):
            frameLayer = BytesIO()
            headerLayer = BytesIO()
            footerLayer = BytesIO()
            mergedLayers = BytesIO()

            createFrame(frameLayer, examData.code, examData.date, '{}/{}'.format(page + 1, self._pages), self._pagesize)

            logoPath = os.path.join(dataPath, 'logo_small.svg')

            createHeader(headerLayer, logoPath, objectData.accred, self._pagesize)

            participants = objectData.participants

            footerLines = len(participants) + 1
            footerLineHeight = 6

            createFooter(footerLayer, participants, footerLines, footerLineHeight, self._pagesize)

            contentLayer = self.page(page, objectData, examData)

            mergeFirstPage(mergedLayers, frameLayer, headerLayer, footerLayer, contentLayer)

            pages.append(mergedLayers)

        appendPages(self._path, *pages)


class StampReport(Report):
    """ Шаблон для протокола испытания мерзлого грунта шариковым штампом """

    def __init__(self, path, pagesize=None):
        super().__init__(path, 2, pagesize)

    def title(self):
        return self.heading(heading_title)

    def content(self, number, objectData, examData):
        i = number

        def grayRows(n):
            return lambda r, c, d: Cell(d, 1, 1, gray) if r < n else d

        table = examData.tables[number]

        if number == i:  # страница 1
            table = formatStampTable2(table)
            r = RTable()
            table = mapTable(table, grayRows(1))
            r.table(table)
            table, spans, background = r.paragraph(alwaysTrue).alignCenter().build()
            av_row = len(table) - 1
            outline = [('OUTLINE', (0, 0), (-1, -1), 1, colors.black)]
            tableStyle = TableStyleBuilder().grid().alignCenter().build(spans, background, outline)

            return Table(table, style=tableStyle, colWidths=scales)

        return Spacer(cm, cm)


def formatStampTable3(table):
    table = [table[0]]
    for i in range(1, len(table)):
        table.append(table[i][0])

    table = adjustedTable(table)

    table = transpose(table)

    table = mapTable(table, lambda r, c, d: ruWithPrec(d, 2 if c == 0 else 3, ""))

    # header0 = ['№ исп.']
    # header1 = ['Время, ч']
    # for i in range(int(columnCount(table)/2)):
    # header0 += [str(i+1), None]
    # header1 += ['l, мм', 'C<sub rise="0.5" size="6">eq</sub>, МПа']

    table = table

    return table


def formatStampTable1(table_):
    table = [table_[0]]
    for i in range(1, len(table_)):
        table.append(table_[i][0])

    table = adjustedTable(table)

    table = transpose(table)

    table = mapTable(table, lambda r, c, d: ruWithPrec(d, 2 if c == 0 else 3, ""))

    # header0 = ['№ исп.']
    # header1 = ['Время, ч']
    # for i in range(int(columnCount(table)/2)):
    # header0 += [str(i+1), None]
    # header1 += ['l, мм', 'C<sub rise="0.5" size="6">eq</sub>, МПа']

    table = table

    return table


def formatStampTable2(table):
    table = mapTable(table, lambda r, c, d: ruWithPrec(d, 3) if c > 0 else d)
    table = [titles] + table
    return table


def testStampReport(objectData, examData):
    """ Функция для тестирования StampReport """
    initFonts()
    report = StampReport(path_save, pagesize=landscape(A4))
    report.build(objectData, examData)


def save_report(titles1, data1, scales1, data_report1, customer_data_info1,
                customer_data1, heading_title1, path_save1,
                code_report="", save_file_name = 'Файл_Отчёт.pdf',
                accred1=None):
    # глобальные переменные
    # Шапка у информации о заказчиках и их объектах
    if accred1 is None:
        accred1 = {'acrreditation': 'AO', 'acrreditation_key': 'новая'}
    global customer_data_info
    customer_data_info = customer_data_info1
    # Сама информация о заказчиках и их объектах
    global customer_data
    customer_data = customer_data1
    # НЕ ТРОГАЙ ! Это переменные для моих расчётов кол-во строк и отрисовка таблиц.. Это заказчики
    global customer_data_zakazchik
    customer_data_zakazchik = ['', '']
    # ТОЖЕ НЕ ТРОГАЙ ! Это Объект
    global customer_data_object
    customer_data_object = ['', '']
    # ТОЖЕ НЕ ТРОГАЙ ! Отвечает за перемычку между отчётами
    global type_format
    type_format = 0
    # Путь сохранения
    global path_save
    # path_save = "C:/Users/Пользователь/YandexDisk/Work/Rabochie versii/itog/Файл_Отчёт.pdf"
    # print(path_save1)
    path_save = path_save1 + '/' +save_file_name

    # Шапочка для нашей таблицы
    global titles
    titles = titles1
    # # Таблица (информация для неё)
    global data
    data = data1
    # # Размер ячеек по ширине
    global scales
    scales = scales1
    # Дата отчёта
    data_report = data_report1.strftime("%d.%m.%Y")
    # Код отчёта

    # print(heading_title1)
    global heading_title
    heading_title = heading_title1


    '''
    Суть всех тут if else и т.д заключается в том, что если в объекте
    или в заказчике слов меньше чем 58 символов, то он не будет затрагивать
    вторую строку и не будет делить элемент на 2 части.
    ------
    Если будет больше чем 58 и при этом меньше 119, то врубается второй столбец,
    элемент делится ровно на две части (по возможности поделит на пробеле).
    Работает это отдельно... тоесть если заказчик будет 40 символов, то будет две строги
    и в этот момент если будет 100 символов в объекте, то он поделится...
    -------
    И самое главное... Если символов в объекте или заказчике будет привышать 119 символов.
    то включается перемычка (type_format = 1) и всё... Удаляется таблица у шапки, стираются границы
    и взамен него отрисовывается новая таблица под шапкой индитична, но тогда в одну строку будет
    доступен ввод ДО +- 210 СИМВОЛОВ!! 
    В случае, если на один из элементов оказался даже больше 210 символов, то ничего страшного,
    отчёт даёт возможность создать ещё одну строку и тогда на ячейку будет уже +- 420 символов, 
    что обязательно должно хватить.
    ________
    P.S 
        Я максимально сделал, чтоб не вылетало и не выбивало отчёт в случае чего.
        для этих двух ячеек по идеи на 840 символов должно хватить наверняка.
        Если не хватит то ...
        "
        from reportlab import xrange
        if type_format == 1:
        pod_mass = [data[d:d + 26] for d in xrange(0, len(data), 26)]
        else:
        pod_mass = [data[d:d + 31] for d in xrange(0, len(data), 31)]
        "
        Найдите код, который выше написан и поменяйте цифру в верхнем pod_mass... Надо менять две цифры!
        если не хватит, то просто ставите 25 и 25 и должно уже точно хватить!
    '''



    if len(customer_data[1]) < 54:
        customer_data_object = [customer_data[1],'']

    elif len(customer_data[1]) < 110:
        customer_data_object = wrap(customer_data[1], math.ceil((len(customer_data[1]) / 2)))

    else:
        customer_data_info = ['','']
        customer_data_zakazchik = ['','']
        customer_data_object = ['','']
        type_format = 1
    if len(customer_data[0]) < 54:
        customer_data_zakazchik = [customer_data[0],'']

    elif len(customer_data[0]) < 110:
        customer_data_zakazchik = wrap(customer_data[0], math.ceil((len(customer_data[0]) / 2)))

    else:
        customer_data_info = ['','']
        customer_data_zakazchik = ['','']
        customer_data_object = ['','']
        type_format = 1

    from reportlab import xrange
    global pod_mass
    if type_format == 1:
        pod_mass = [data[d:d + 21] for d in xrange(0, len(data), 21)]
        if len(pod_mass[-1]) < 3:
            pod_mass = [data[d:d + 21-2] for d in xrange(0, len(data), 21-2)]
    else:
        pod_mass = [data[d:d + 23] for d in xrange(0, len(data), 23)]
        if len(pod_mass[-1]) < 3:
            pod_mass = [data[d:d + 23-2] for d in xrange(0, len(data), 23-2)]

    # Делитель таблицы
    all_table = []
    i = 0
    while i <= len(pod_mass) - 1:
        all_table.append(pod_mass[i])
        i = i + 1

    # Данные о таблице
    examData = AttrDict({
        'code': code_report,
        'date': data_report,
        'tables': all_table,

    })
    # Шапочка
    if accred1:
        accred = [accreditation[accred1['accreditation']][accred1['accreditation_key']][0],
                  accreditation[accred1['accreditation']][accred1['accreditation_key']][1]]
    else:
        accred = [
            'АТТЕСТАТ АККРЕДИТАЦИИ №RU.MCC.АЛ.988 Срок действия с 09 января 2020г.',
            'РЕЕСТР ГЕОНАДЗОРА г. МОСКВЫ №27 (РЕЙТИНГ №4)'
        ]
    # Исполнители
    participants = [
        ["Исполнители:",
         "Жмылёв Д.А., Старостин П.А., Чалая Т.А., Михалева О.В., Горшков Е.С., Доронин С.А."],
        ["Исполнительный директор / нач. ИЛ:", "Семенова О.В."],
        ["Научный руководитель ИЛ:", "Академик РАЕН Озмидов О.Р. / к.т.н. Череповский А.В."],
        ["Главный инженер:", "Жидков И.М."]
    ]
    objectData = AttrDict({
        'accred': accred,
        'participants': participants,
    })
    testStampReport(objectData, examData)



if __name__ == "__main__":
    # # Шапка у информации о заказчиках и их объектах
    # customer_data_info1 = ['Заказчик:', 'Объект:']
    # # Сама информация о заказчиках и их объектах
    # customer_data1 = ['Многофункциональный customer data zakazchik customer data zakazchik customer data',
    #                  'Многофункционал 1313 222  2222 2 2 2  22 2 2 2 2 2 2  2 2 21 2 21124 424 1231 212121 213213 231312 13 2 666 hello my browser loves']
    # # Шапочка для нашей таблицы
    # titles1 = ['Лаб.номер', 'Скважина', 'Глубина']
    # # # Таблица (информация для неё)
    # data1 = [
    #     ['2-1', '2.00', '1'], ['2-2', '2.00', '1'], ['2-3', '2.00', '2'], ['2-4', '2.00', '4'], ['2-6', '2.00', '16'], [
    #         '2-7', '2.00', '22'], ['2-8', '2.00', '27'], ['3-1', '3.00', '1'], ['3-2', '3.00', '2'], ['3-3', '3.00',
    #                                                                                                   '4'], ['3-4',
    #                                                                                                          '3.00',
    #                                                                                                          '7'], [
    #         '3-5', '3.00', '10'], ['3-6', '3.00', '12'], ['3-7', '3.00', '14'], ['3-8', '3.00', '14'], ['3-9', '3.00',
    #                                                                                                     '19'], ['3-10',
    #                                                                                                             '3.00',
    #                                                                                                             '20'], [
    #         '3-11', '3.00', '22'], ['3-12', '3.00', '24'], ['5-1', '5.00', '8'], ['5-2', '5.00', '15'], ['5-3', '5.00',
    #                                                                                                      '24'], ['6-1',
    #                                                                                                              '6.00',
    #                                                                                                              '1'], [
    #         '6-2', '6.00', '3'], ['6-3', '6.00', '4'], ['6-4', '6.00', '8'], ['6-5', '6.00', '14'], ['6-6', '6.00',
    #                                                                                                  '16'], ['6-7',
    #                                                                                                          '6.00',
    #                                                                                                          '18'], [
    #         '6-8', '6.00', '23']]
    # # # Размер ячеек по ширине
    # scales1 = [3 * cm, 5 * cm, 6 * cm]
    # # Дата отчёта
    # data_report1 = '27.04.2021'
    #
    # save_report(titles1, data1, scales1, data_report1, customer_data_info1, customer_data1)


    # глобальные переменные
    # Шапка у информации о заказчиках и их объектах
    customer_data_info = ['Заказчик:', 'Объект:']
    # Сама информация о заказчиках и их объектах
    customer_data = ['Многофункциональный customer data zakazchik customer data zakazchik customer data',
                     'Многофункционал 1313 222  2222 2 2 2  22 2 2 2 2 2 2  2 2 21 2 21124 424 1231 212121 213213 231312 13 2 666 hello my browser loves']
    # НЕ ТРОГАЙ ! Это переменные для моих расчётов кол-во строк и отрисовка таблиц.. Это заказчики
    customer_data_zakazchik = ['', '']
    # ТОЖЕ НЕ ТРОГАЙ ! Это Объект
    customer_data_object = ['', '']
    # ТОЖЕ НЕ ТРОГАЙ ! Отвечает за перемычку между отчётами
    type_format = 0
    # Путь сохранения
    path_save = "C:/Users/kossc/YandexDisk/2. Работа/Ktcz/Файл_Отчёт.pdf"
    # Шапочка для нашей таблицы
    titles = ['Лаб.номер', 'Скважина', 'Глубина']
    # Таблица (информация для неё)
    data = [
        ['2-1', '2.00', '1'], ['2-2', '2.00', '1'], ['2-3', '2.00', '2'], ['2-4', '2.00', '4'], ['2-6', '2.00', '16'], [
            '2-7', '2.00', '22'], ['2-8', '2.00', '27'], ['3-1', '3.00', '1'], ['3-2', '3.00', '2'], ['3-3', '3.00',
                                                                                                      '4'], ['3-4',
                                                                                                             '3.00',
                                                                                                             '7'], [
            '3-5', '3.00', '10'], ['3-6', '3.00', '12'], ['3-7', '3.00', '14'], ['3-8', '3.00', '14'], ['3-9', '3.00',
                                                                                                        '19'], ['3-10',
                                                                                                                '3.00',
                                                                                                                '20'], [
            '3-11', '3.00', '22'], ['3-12', '3.00', '24'], ['5-1', '5.00', '8'], ['5-2', '5.00', '15'], ['5-3', '5.00',
                                                                                                         '24'], ['6-1',
                                                                                                                 '6.00',
                                                                                                                 '1'], [
            '6-2', '6.00', '3'], ['6-3', '6.00', '4'], ['6-4', '6.00', '8'], ['6-5', '6.00', '14'], ['6-6', '6.00',
                                                                                                     '16'], ['6-7',
                                                                                                             '6.00',
                                                                                                             '18'], [
            '6-8', '6.00', '23']]
    # Размер ячеек по ширине
    scales = [3 * cm, 5 * cm, 6 * cm]
    # Дата отчёта
    data_report = '27.04.2021'
    # Код отчёта
    code_report = '23-dosfs328941FF'

    '''
    Суть всех тут if else и т.д заключается в том, что если в объекте
    или в заказчике слов меньше чем 58 символов, то он не будет затрагивать
    вторую строку и не будет делить элемент на 2 части.
    ------
    Если будет больше чем 58 и при этом меньше 119, то врубается второй столбец,
    элемент делится ровно на две части (по возможности поделит на пробеле).
    Работает это отдельно... тоесть если заказчик будет 40 символов, то будет две строги
    и в этот момент если будет 100 символов в объекте, то он поделится...
    -------
    И самое главное... Если символов в объекте или заказчике будет привышать 119 символов.
    то включается перемычка (type_format = 1) и всё... Удаляется таблица у шапки, стираются границы
    и взамен него отрисовывается новая таблица под шапкой индитична, но тогда в одну строку будет
    доступен ввод ДО +- 210 СИМВОЛОВ!!
    В случае, если на один из элементов оказался даже больше 210 символов, то ничего страшного,
    отчёт даёт возможность создать ещё одну строку и тогда на ячейку будет уже +- 420 символов,
    что обязательно должно хватить.
    ________
    P.S
        Я максимально сделал, чтоб не вылетало и не выбивало отчёт в случае чего.
        для этих двух ячеек по идеи на 840 символов должно хватить наверняка.
        Если не хватит то ...
        "
        from reportlab import xrange
        if type_format == 1:
        pod_mass = [data[d:d + 26] for d in xrange(0, len(data), 26)]
        else:
        pod_mass = [data[d:d + 31] for d in xrange(0, len(data), 31)]
        "
        Найдите код, который выше написан и поменяйте цифру в верхнем pod_mass... Надо менять две цифры!
        если не хватит, то просто ставите 25 и 25 и должно уже точно хватить!
    '''

    if len(customer_data[1]) < 58:
        customer_data_object = [customer_data[1], '']

    elif len(customer_data[1]) < 119:
        customer_data_object = wrap(customer_data[1], math.ceil((len(customer_data[1]) / 2)))

    else:
        customer_data_info = ['', '']
        customer_data_zakazchik = ['', '']
        customer_data_object = ['', '']
        type_format = 1
    if len(customer_data[0]) < 58:
        customer_data_zakazchik = [customer_data[0], '']

    elif len(customer_data[0]) < 119:
        customer_data_zakazchik = wrap(customer_data[0], math.ceil((len(customer_data[0]) / 2)))

    else:
        customer_data_info = ['', '']
        customer_data_zakazchik = ['', '']
        customer_data_object = ['', '']
        type_format = 1

    from reportlab import xrange

    if type_format == 1:
        pod_mass = [data[d:d + 26] for d in xrange(0, len(data), 26)]
    else:
        pod_mass = [data[d:d + 31] for d in xrange(0, len(data), 31)]

    # Делитель таблицы
    all_table = []
    i = 0
    while i <= len(pod_mass) - 1:
        all_table.append(pod_mass[i])
        i = i + 1

    # Данные о таблице
    examData = AttrDict({
        'code': code_report,
        'date': data_report,
        'tables': all_table,

    })
    heading_title = 'ХОЛА'
    # Шапочка
    accred = [
        'АТТЕСТАТ АККРЕДИТАЦИИ №RU.MCC.АЛ.988 Срок действия с 09 января 2020г.',
        'РЕЕСТР ГЕОНАДЗОРА г. МОСКВЫ №27 (РЕЙТИНГ №4)'
    ]
    # Исполнители
    participants = [
        ["Исполнители:",
         "Жмылёв Д.А., Старостин П.А., Чалая Т.А., Чипеев С.С. Михалева О.В., Горшков Е.С., Доронин С.А."],
        ["Исполнительный директор / нач. ИЛ:", "Семенова О.В."],
        ["Научный руководитель ИЛ:", "Академик РАЕН Озмидов О.Р. / к.т.н. Череповский А.В."],
        ["Техн. директор:", "Жидков И.М."]
    ]
    objectData = AttrDict({
        'accred': accred,
        'participants': participants,
    })
    testStampReport(objectData, examData)
    sys.exit()

'''
version 2.1 
1) fix table in cap
2) add line our MDGT
3) fix row in table
4) edit info "Исполнители"

Version 2.0 --old
1) create and fix table zakazchiki
2) delete garbage
3) write comment's
4) Iterating through
            math when calc. element in an massive "customer_data"

'''


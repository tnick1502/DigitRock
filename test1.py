import os

s = "Z:/МДГТ - (Заказчики)/ПетроБурСервис ООО/2023/246-23 Судоремонтная верфь Рем-Нова ДВ/2. в работе/G0/246-23 Судоремонтная верфь Рем-Нова ДВ - plaxis.xls"
"162-23- ГКС Сахалин - мех.xls"
""
""

name = os.path.split(s)[-1]
name = name[name.index(" ") + 1: len(name) - name[::-1].index("-") - 1].strip()


print(name)

PhysicalPropertyPosition = {
    "laboratory_number": ["A", 0],
    "borehole": ['B', 1],
    "depth": ['C', 2],
    "soil_name": ['D', 3],
    "ige": ['ES', 148],
    "rs": ['P', 15],
    "r": ['Q', 16],
    "rd": ['R', 17],
    "n": ['S', 18],
    "e": ['T', 19],
    "W": ['U', 20],
    "Sr": ['V', 21],
    "Wl": ['W', 22],
    "Wp": ['X', 23],
    "Ip": ['Y', 24],
    "Il": ['Z', 25],
    "Ir": ['AE', 30],
    "stratigraphic_index": ['AH', 34],
    "ground_water_depth": ['AJ', 35],
    "granulometric_10": ['E', 4],
    "granulometric_5": ['F', 5],
    "granulometric_2": ['G', 6],
    "granulometric_1": ['H', 7],
    "granulometric_05": ['I', 8],
    "granulometric_025": ['J', 9],
    "granulometric_01": ['K', 10],
    "granulometric_005": ['L', 11],
    "granulometric_001": ['M', 12],
    "granulometric_0002": ['N', 13],
    "granulometric_0000": ['O', 14],
    "Rc": ['ER', 147],
    "date": ['IF', 239],
    "new_laboratory_number": ["IG", 240],
    "description": ["AR", 43]
}

MechanicalPropertyPosition = {
    "build_press": ['AK', 36],
    "pit_depth": ['AL', 37],
    "OCR": ["GB", 183],
    "Cv": ["CC", 80],
    "Ca": ["CF", 83],
    "K0nc": ["GZ", 207],
    "K0oc": ["GY", 206],
    "Nuur": ["HA", 208],
    "K0ige": ["FW", 178],
    "pressure_array": ["BO", 66],
    "Eoed": ["CE", 82],
    "Pref": ["FV", 177],
    "p_max": ["CV", 99],
    "Eur": ["GI", 190],
    "c_res": ["CV", 99],
    "fi_res": ["CW", 100]
}

c_fi_E_PropertyPosition = {
    "Трёхосное сжатие (E)": [["BI", "BJ", "BK"], [60, 61, 62]],
    "Трёхосное сжатие (F, C)": [["BF", "BG", "BH"], [57, 58, 59]],
    "Трёхосное сжатие (F, C, E)": [["BC", "BD", "BE"], [54, 55, 56]],
    "Трёхосное сжатие (F, C) res": [["BF", "BG", "BH"], [57, 58, 59]],
    "Трёхосное сжатие (F, C, Eur)": [["BF", "BG", "BN"], [57, 58, 65]],
    "Трёхосное сжатие КН": [["CO", "CP", "CQ", "CR"], [92, 93, 94, 95]],
    "Трёхосное сжатие НН": [["CK", "CL", "CM"], [88, 89, 90]],
    "Трёхосное сжатие с разгрузкой": [["BL", "BM", "BN"], [63, 64, 65]],
    "Трёхосное сжатие с разгрузкой (plaxis)": [["BL", "BM", "BN"], [63, 64, 65]],
    "Сейсморазжижение": [["BY", "BZ", "CA"], [76, 77, 78]],
    "Потенциал разжижения": [["BY", "BZ", "CA"], [76, 77, 78]],
    "Динамическая прочность на сдвиг": [["BY", "BZ", "CA"], [76, 77, 78]],
    "Штормовое разжижение": [["BY", "BZ", "CA"], [76, 77, 78]],
    "Демпфирование": [["BY", "BZ", "CA"], [76, 77, 78]],
    "По заданным параметрам": [["BY", "BZ", "CA"], [76, 77, 78]],
    "Виброползучесть": [["BS", "BT", "BU"], [70, 71, 72]],
    "Снижение модуля деформации сейсмо": [["BS", "BT", "BU"], [70, 71, 72]],
    "Резонансная колонка": [["HM", "HN", "HO"], [220, 221, 222]],
    "Срез природное": [["AV", "AW"], [47, 48]],
    "Срез водонасыщенное": [["AS", "AT"], [44, 45]],
    "Срез плашка по плашке": [["AY", "AZ"], [50, 51]],
    "Срез НН": [["BA", "BB"], [52, 53]],
    "Срез дилатансия": [["HB", "HC", "HE"], [209, 210, 212]],
    "Вибропрочность": [["BC", "BD", "BE", "CR"], [54, 55, 56, 95]],
    "Демпфирование по Релею": [["BY", "BZ", "CA"], [76, 77, 78]],
}

DynamicsPropertyPosition = {
    "magnitude": ["AQ", 42],
    "intensity": ["AM", 38],
    "reference_pressure": ["FV", 177],
    "acceleration": ["AP", 41],
    "rw": ["HU", 228],
    "Hw": ["HS", 226],
    "frequency_storm": ["HT", 227],
    "cycles_count_storm": ["HR", 225],
    "frequency_vibration_creep": ["AN", 39],
    "Kd_vibration_creep": ["CB", 79],
    "sigma_d_vibration_creep": ["AO", 40],
    "sigma_1": ["FU", 176],
}

IdentificationColumns = {
    "Резонансная колонка": 219,
    "Сейсморазжижение": 230,
    "Штормовое разжижение": 230,
}

GeneralDataColumns = {
    "customer": ["A1", (0, 0)],
    "object_name": ["A2", (1, 0)],
    "end_date": ["Q1", (0, 16)],
    "start_date": ["U1", (0, 20)],
    "accreditation": ["I2", (1, 8)],
    "object_number": ["AI1", (0, 34)],
    "shipment_number": ["J2", (1, 9)]
}

K0Columns = {
    "nc": ["GZ", 207],
    "ocr": ["GY", 206],
    "ige": ["FW", 178]
}
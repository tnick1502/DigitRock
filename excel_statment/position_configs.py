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
    "date": ['IF', 239]
}

MechanicalPropertyPosition = {
    "build_press": ['AK', 36],
    "pit_depth": ['AL', 37],
    "OCR": ["GB", 183],
    "Cv": ["CC", 80],
    "Ca": ["CF", 83],
    "K0nc": ["GZ", 207],
    "K0oc": ["GY", 206],
    "pressure_array": ["BO", 66],
    "Eoed": ["CE", 82],
    "p_max": ["CV", 99]
}

c_fi_E_PropertyPosition = {
    "Трёхосное сжатие (E)": [["BI", "BJ", "BK"], [60, 61, 62]],
    "Трёхосное сжатие (F, C)": [["BF", "BG", "BH"], [57, 58, 59]],
    "Трёхосное сжатие (F, C, E)": [["BC", "BD", "BE"], [54, 55, 56]],
    "Трёхосное сжатие с разгрузкой": [["BL", "BM", "BN"], [63, 64, 65]],
    "Сейсморазжижение": [["BY", "BZ", "CA"], [76, 77, 78]],
    "Штормовое разжижение": [["BY", "BZ", "CA"], [76, 77, 78]],
    "Демпфирование": [["BY", "BZ", "CA"], [76, 77, 78]],
    "Виброползучесть": [["BS", "BT", "BU"], [70, 71, 72]],
    "Резонансная колонка": [["BC", "BD", "BE"], [54, 55, 56]]
}

DynamicsPropertyPosition = {
    "magnitude": ["AQ", 42],
    "intensity": ["AM", 38],
    "reference_pressure": ["FV", 177],
    "acceleration": ["AP", 41],
    "rw": ["HU", 228],
    "Hw": ["HS", 226],
    "frequency_storm": ["HT", 227],
    "cycles_count_storm": ["HT", 225],
    "frequency_vibration_creep": ["AN", 39],
    "Kd_vibration_creep": ["CB", 79],
    "sigma_d_vibration_creep": ["AO", 40],
}

IdentificationColumns = {
    "Резонансная колонка": 219,
    "Сейсморазжижение": 230,
    "Штормовое разжижение": 230,
}
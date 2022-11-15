_debug = [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
             "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32"],
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
             "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32"]]

def create_dev_table(Data):
    if len(Data[0]) < 42:
        Data[0]=Data[0]+["-"]*(42-len(Data[0]))
        Data[1] = Data[1] + ["-"] * (42 - len(Data[1]))
    print('Data', Data[0], Data[1])

    base_cicl = []
    new_Data = []

    One, Two = Data
    head = ['№ п/п', 'Время, мин', 'Отн. деформация ε1, д.е.']

    for D in range(len(Data[0])):

        if D <= 13:
            base_cicl.append(str(D + 1))
            base_cicl.append(One[D])
            base_cicl.append(Two[D])
            new_Data.append(base_cicl)
            base_cicl = []
        elif D <= 27 and D > 14:
            base_cicl.append(str(D + 1))
            base_cicl.append(One[D])
            base_cicl.append(Two[D])
            for i in range(len(base_cicl)):
                new_Data[D - 14].append(base_cicl[i])
            base_cicl = []
        else:
            base_cicl.append(str(D + 1))
            base_cicl.append(One[D])
            base_cicl.append(Two[D])
            for i in range(len(base_cicl)):
                new_Data[D - 28].append(base_cicl[i])
            base_cicl = []
    _b = []
    _b.append(head * 3)
    _b.append(new_Data)
    return _b

base = create_dev_table(_debug)
print(base)
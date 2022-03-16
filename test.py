
import hashlib
def hash_id(labolatory_number: str, object_number: str):
    hash_object = hashlib.sha1(f"{object_number} {labolatory_number}".encode("utf-8"))
    return hash_object.hexdigest()







data = [['16-2', '16.0', '2.5', 'Песок пылеватый однородный', '40,0; 60,0', '20,3; 19,2; ', '15,0; 13,4; ', '0,74; 0,70; '],
        ['16-3', '16.0', '5.0', 'Песок мелкий однородный', '40,0; 60,1', '32,6; 34,7; ', '25,1; 26,1; ', '0,77; 0,75; '],
        ['16-4', '16.0', '7.5', 'Песок пылеватый однородный', '40,0; 60,2', '25,4; 23,9; ', '18,8; 16,8; ', '0,74; 0,70; '],
        ['16-7', '16.0', '13.5', 'Песок мелкий однородный', '40,0; 60,3', '42,4; 38,5; ', '33,2; 29,4; ', '0,78; 0,76; '],
        ['16-11', '16.0', '22.0', 'Песок мелкий неоднородный', '40,0; 60,4', '51,0; 47,2; ', '41,1; 35,8; ', '0,80; 0,76; '],
        ['27-6', '27.0', '10.5', 'Песок мелкий однородный', '40,0; 60,5', '36,2; 36,6; ', '28,3; 27,4; ', '0,78; 0,75; '],
        ['27-8', '27.0', '15.5', 'Песок мелкий неоднородный', '40,0; 60,6', '41,5; 42,9; ', '32,3; 32,7; ', '0,78; 0,76; '],
        ['27-9', '27.0', '17.5', 'Песок мелкий неоднородный', '40,0; 60,7', '44,4; 44,0; ', '34,3; 34,2; ', '0,77; 0,78; '],
        ['30-6', '30.0', '10.7', 'Песок пылеватый однородный', '40,0; 60,8', '28,8; 28,5; ', '21,1; 20,1; ', '0,73; 0,71; '],
        ['30-8', '30.0', '14.7', 'Песок пылеватый однородный', '40,0; 60,9', '33,4; 33,4; ', '25,5; 23,9; ', '0,76; 0,72; '],
        ['30-12', '30.0', '22.7', 'Песок пылеватый однородный', '40,0; 60,10', '37,1; 37,1; ', '27,6; 26,2; ', '0,74; 0,71; '],
        ['30-13', '30.0', '24.7', 'Песок мелкий однородный', '40,0; 60,11', '48,1; 46,4; ', '37,4; 35,5; ', '0,78; 0,77; '],
        ['38-12', '38.0', '25.0', 'Песок пылеватый однородный', '40,0; 60,12', '34,2; 32,9; ', '25,6; 23,9; ', '0,75; 0,73; '],
        ['38-13', '38.0', '26.0', 'Супесь пластичная пылеватая', '40,0; 60,13', '36,0; 36,4; ', '31,9; 30,2; ', '0,88; 0,83; '], ['']]


def convert_data(data):
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

    def val_to_list(val, prec) -> list:
        if val is None:
            return None
        else:
            try:
                val = [float(val)]
            except ValueError:
                v = val.split(";")
                val = []
                for value in v:
                    try:
                        a = float(value.replace(",", ".").strip(" "))
                        a = zap(a, prec)
                        val.append(a)
                    except:
                        pass

            return val

    data_new = []

    for i in range(len(data)):
        try:
            line = data[i]
            borehole = float(line[1])
            if borehole % 1 < 0.001:
                line[1] = str(int(borehole))
            else:
                line[1] = str(borehole)

            line[2] = line[2].replace(".", ",")# zap(line[2], 1, none='-')
        except IndexError:
            pass

        try:
            if len(val_to_list(line[5], 1)) > 0:
                f = val_to_list(line[4], 1)
                E50 = val_to_list(line[5], 1)
                Ed = val_to_list(line[6], 1)
                Kd =val_to_list(line[7], 2)

                line = [line[0], line[1], line[2], line[3], f[0], E50[0], Ed[0], Kd[0]]
                data_new.append(line)

                for j in range(1, len(f)):
                    line = [line[0], line[1], line[2], line[3], f[j], E50[j], Ed[j], Kd[j]]
                    data_new.append(line)
            else:
                data_new.append(line)
        except:
            data_new.append(line)

    return data_new



    #x.insert(val, pos)

a = convert_data(data)

for i in a:
    print(i)
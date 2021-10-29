num = 80


def str_Kf(x):
    s = "{:.2e}".format(x).replace(".", ",")
    return s[:-4], str(int(s[5:]))

print(str_Kf(0.005))
def float_df(x):
    if str(x) != "nan" and str(x) != "NaT":
        try:
            return float(x)
        except ValueError:
            return x
        except TypeError:
            return x
    else:
        return None

def str_df(x):
    if str(x) != "nan" and str(x) != "NaT":
        return str(x)
    else:
        return None


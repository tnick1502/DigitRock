
x = "1; 6"

m = [float(x)] if str(x).isdigit() else list(map(lambda x: float(x.replace(",", ".").strip(" ")), x.split(";")))

print(m)
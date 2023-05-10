

s = 'ООО "ЦИИАК"'
castomer_name = ''.join(list(filter(lambda c: c not in '\/:*?"<>|', s)))


#castomer_name = s.translate('\/:*?"<>|')
print(castomer_name)
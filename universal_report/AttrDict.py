
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

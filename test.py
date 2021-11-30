import time

def decorator(**kwargs):
    def wrapper(*args, **kwargs):
        wrapper.cals += 1
        print(wrapper.cals)
        return f(*args)
    wrapper.cals = 0
    return wrapper

def delegate_str(aClass):

    class wrap:
        def __init__(self, *args, **kwargs):
            self.wrapped = aClass(*args, **kwargs)
        def __getattr__(self, item):
            print("wrap")
            return getattr(self.wrapped, item)
    return wrap



class tracer:
    def __init__(self, func) : # При декорировании сохранение исходной функции
        self.calls = 0
        self.func = func
    def __call__(self, *args) : # При последующих вызовах: запуск исходной функции
        self.calls += 1
        print(self.calls)
        return self.func(*args)

@delegate_str
class Person:
    def __init__ (self, name, pay) :
        self.name = name
        self.pay = pay
    #@decorator
    def giveRaise(self, percent): # giveRaise = tracer (giveRaise)
        self.pay *= (1.0 + percent)



import numpy as np
x = 1.15
a = np.log10(x + 1)
print(10**a - 1)


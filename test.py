import time

def decorator(f):
    def wrapper(*args):
        wrapper.cals += 1
        print(wrapper.cals)
        return f(*args)
    wrapper.cals = 0
    return wrapper


class tracer:
    def __init__(self, func) : # При декорировании сохранение исходной функции
        self.calls = 0
        self.func = func
    def __call__(self, *args) : # При последующих вызовах: запуск исходной функции
        self.calls += 1
        print(self.calls)
        return self.func(*args)

class Person:
    def __init__ (self, name, pay) :
        self.name = name
        self.pay = pay
    #@decorator
    def giveRaise(self, percent): # giveRaise = tracer (giveRaise)
        self.pay *= (1.0 + percent)

from abc import abstractmethod, ABCMeta


class BaseProcessor(metaclass=ABCMeta):
    """Абстрактный суперкласс обработчика
        Суперкласс принимает объект модели и формирует из данных опыта данные для постоения"""
    def __init__(self, obj):
        self.obj = obj

    @abstractmethod
    def ыу(self):
        while False:
            yield None
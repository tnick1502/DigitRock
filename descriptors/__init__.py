class DataTypeValidation:
    """Дескриптор для валидации данных"""

    def __init__(self, *args):
        self.data_types = args

    def __set_name__(self, owner, name):
        self.attr = name

    def __set__(self, instance, value):
        if value is None:
            instance.__dict__[self.attr] = value
        elif any(isinstance(value, i) for i in self.data_types):
            instance.__dict__[self.attr] = value
        else:
            raise ValueError(f"{value} must be a {str(self.data_types)} but it is {str(type(value))}")

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.attr, None)

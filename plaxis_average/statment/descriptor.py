class DataTypeValidation:
    """Дескриптор для валидации данных

    Проверяет значение на соответствие заданному типу, в случае несовпадения пытается привести к заданному
    типу. При невозможности приведения к типу возбуждает ValueError
    """
    data_type: object = None

    def __init__(self, *args):
        self.data_type = args[0]

    def __set_name__(self, owner, name):
        self.attr = name

    def __set__(self, instance, value):
        if value is None:
            instance.__dict__[self.attr] = value
        else:
            if isinstance(value, self.data_type):
                instance.__dict__[self.attr] = value
            else:
                try:
                    instance.__dict__[self.attr] = self.data_type(value)
                except:
                    raise ValueError(f"value of '{self.attr}' is '{value}' ({str(type(value))}), it's type must be {str(self.data_type)}")

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.attr, None)

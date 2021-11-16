a = type("a", (), {"a": 3, "get_a": lambda self: self.a})

b = a()
print(b.get_a())



class A:
    a = [1,2,3,4,5]

    def __geta__(self, val):
        return self.a[val]

    def __setitem__(self, key, val):
        self.a[key] = val

p = A()

for i in p:
    print(i)
import numpy as np

x = np.hstack((np.linspace(0, 100, 100), np.linspace(0, 100, 100)))

i, = np.where(x > 50)
print(i)

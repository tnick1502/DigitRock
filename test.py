import numpy as np
import matplotlib.pyplot as plt
from numpy.linalg import lstsq


def lse(__y):
    A = np.vstack([np.zeros(len(__y)), np.ones(len(__y))]).T
    k, b = lstsq(A, __y, rcond=None)[0]
    return b

inp_x = [1, 2, 3]
inp_y = [2, 5, 10]

b = lse(inp_y)
b1 = sum(inp_y)/len(inp_y)

x = np.linspace(0, 10)
y = 0*x + b
y1 = 0*x + b1

plt.figure()
plt.plot(x, y)
plt.scatter(inp_x, inp_y)
plt.show()

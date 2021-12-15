import numpy as np
import matplotlib

x = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
y = np.array([0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10])

x = x*x

import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 1)

axes[0].plot(np.log(x + 1), y)

axes[1].plot(x, y)
axes[1].set_xscale("log")

plt.show()

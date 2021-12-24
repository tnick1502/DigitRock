"""import numpy as np
import matplotlib

x = -np.linspace(0.1, 1000,  1000)
y = -np.linspace(0.1, 1000,  1000)

x = x*x

import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 1)

axes[0].plot(np.log10(x + 1), y)


def define_sticks(x):
    values = np.array([1, 10, 100, 1000, 10000, 100000, 1000000])
    values = np.hstack((np.array([-1]), np.log10(values)))
    text = ["$10^{-1}$", "$10^{0}$", "$10^{1}$", "$10^{2}$", "$10^{3}$", "$10^{4}$",
            "$10^{5}$", "$10^{6}$"]
    for i in range(len(values)):
        if values[i] > x:
            break
    return values[:i+1], text[:i+1]

stick, text = define_sticks(x[-1])
stick[0] = -1
axes[0].set_xticks(stick)
axes[0].set_xticklabels(text)


axes[1].plot(x, y)
axes[1].set_xscale("log")

plt.show()"""
import numpy as np
s = [0, 5, 6,8 ,7,5,9,9,8,1]
m = [int(i) for i in range(0, len(s), int(len(s)/(5-2)))] + [len(s)]
print(m)
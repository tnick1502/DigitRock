import matplotlib.pyplot as plt

fig = plt.figure()

ax_1 = fig.add_subplot(2, 1, 1)
ax_2 = fig.add_subplot(4, 1, 4)

plot_params = {"right": 0.98, "top": 0.98, "bottom": 0.05, "wspace": 0.05, "hspace": 0, "left": 0.1}
plt.subplots_adjust(**plot_params)


plt.show()
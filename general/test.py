import numpy as np
import matplotlib.pyplot as plt
from general.general_functions import logarithm, sigmoida, mirrow_element

x = np.linspace(0, 1, 20000)

y = sigmoida(mirrow_element(x, 0.5), 0.6, 0.5, 1, 1.5)

plt.plot(x, y)
plt.show()
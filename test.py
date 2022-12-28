from general.general_functions import sigmoida, mirrow_element
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0.001, 2)

u = sigmoida(mirrow_element(x, 1), 15, 1.8, 18, 2.7)

plt.plot(x, sigmoida(mirrow_element(x, 1), 15, 1.8, 18, 2.7))

plt.show()

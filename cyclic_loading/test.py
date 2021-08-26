
import numpy as np
import matplotlib.pyplot as plt
from general.general_functions import sigmoida, mirrow_element


x = np.linspace(0, 200, 1000)

plt.plot(x, sigmoida(mirrow_element(x, 100), 0.3, 100, 1.1, 250))
plt.show()
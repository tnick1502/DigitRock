import numpy as np
import matplotlib.pyplot as plt
from general.general_functions import sigmoida, mirrow_element


x = np.linspace(0, 1)

y = sigmoida(mirrow_element(x, 0.5), 0.5, 0.5, 0.55, 1.55)

plt.plot(x, y)
plt.show()

import numpy as np
import matplotlib.pyplot as plt
from general.general_functions import sigmoida, mirrow_element


x = np.linspace(0, 1, 100)

plt.plot(x, sigmoida(x, 5, 0.75, 8, 0.5))

#plt.plot(x, sigmoida(mirrow_element(x, 0.75), 5, 0.75, 5, 0.5))
plt.show()
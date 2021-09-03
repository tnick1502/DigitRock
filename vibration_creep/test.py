
import matplotlib.pyplot as plt
from general.general_functions import read_json_file, sigmoida, mirrow_element
import numpy as np


x = np.linspace(0, 100, 1000)


plt.plot(x, sigmoida(mirrow_element(x, 50), 0.1, 40, 0.9, 120))
plt.show()
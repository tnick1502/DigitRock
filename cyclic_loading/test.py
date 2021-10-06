from datetime import datetime
import numpy as np

import numpy as np
import matplotlib.pyplot as plt
from general.general_functions import step_sin, create_acute_sine_array

x = np.linspace(0, 5, 1000)

deviator = np.sin(x*2*np.pi + step_sin(x, -0.03*np.pi, 5, 0.25))

shift = step_sin(x + 0.3/4, 0.1*np.pi, 5, 0.25)

#shift = step_sin(np.linspace(0, 1, 1000), 0.1*np.pi, 0.25, 0.5)

shift = 0
strain = np.sin(x*2*np.pi + step_sin(x + shift/6, 0.12*np.pi, 5, 0.25) + shift)

#plt.plot(x, strain)
plt.plot(x, strain)
plt.plot(x, step_sin(x + shift/6, 0.12*np.pi, 5, 0.25))
#plt.plot(x, shift)

#plt.plot(strain, deviator)
plt.show()


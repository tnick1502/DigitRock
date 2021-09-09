import numpy as np

x = np.linspace(0, 100, 1001)

point_count = 200

k = int(len(x)/point_count)

current_x = [val for i, val in enumerate(x) if i%k == 0]

print(current_x)
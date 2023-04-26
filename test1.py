import datetime
import time
time_1 = datetime.datetime.now()

time.sleep(1)

time_2 = datetime.datetime.now()
print((time_2 - time_1).seconds)
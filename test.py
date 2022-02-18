
import hashlib

def hash_id(labolatory_number: str, object_number: str):
    hash_object = hashlib.sha1(f"{object_number} {labolatory_number}".encode("utf-8"))
    return hash_object.hexdigest()


import matplotlib.pyplot as plt

plt.scatter(0.005, 1.08/2,s = 10, color="black")
plt.show()

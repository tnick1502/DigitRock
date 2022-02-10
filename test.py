
import hashlib

def hash_id(labolatory_number: str, object_number: str):
    hash_object = hashlib.sha1(f"{object_number} {labolatory_number}".encode("utf-8"))
    return hash_object.hexdigest()


lambda: 1

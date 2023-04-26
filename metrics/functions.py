import socket

def user_ip():
    return str(socket.gethostbyname(socket.gethostname()))

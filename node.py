import socket

class Node:
    # Private variables
    ip_addr = "0.0.0.0"

    # Public classes
    # Constructor
    def __init__(self):
        self.data = []

    # Return Hello, World!
    def hello(self):
        return "Hello, World!"

# HOST = '' 
# PORT = 9600

# # Create and INET UDP Socket
# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # socket.SOCK_STREAM would make a TCP connection
# # TCP would also require you to bind then listen to the port while UDP just binds
# s.bind((HOST, PORT))
message = "Disconnected"
client_ip = "127.0.0.1"
# while not data:
#         data, addr = s.recvfrom(1024)
#         if not data:
#             break
#         client_ip = addr
#         message = data
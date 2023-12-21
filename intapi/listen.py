import socket
import json

class NAMserver(object):
    bind = False
    nam_sock = None
    nam_conn = None
    client_addr = None
    @staticmethod
    def bind_socket():
        NAMserver.nam_sock = socket.socket()
        NAMserver.nam_sock.bind(('127.0.0.1', 9090))
        NAMserver.bind = True
    @staticmethod
    def wait_for_conn():
        NAMserver.nam_sock.listen(1)
        NAMserver.nam_conn, NAMserver.client_addr = NAMserver.nam_sock.accept()
        print(f"connect: {NAMserver.client_addr}")

def start_server():
    NAMserver.bind_socket()
    NAMserver.wait_for_conn()

def get_data():
    data = NAMserver.nam_conn.recv(1024)
    return json.loads(data)

def send_data(message, user_name):
    NAMserver.nam_conn.send(bytes(f"new message for user {user_name}: {message}", encoding = 'UTF-8'))


# def send_response(message, user_name):
#     print(f"new reply for user {user_name}: {message}")

# def wait_for_req():
#     user_name = input("user_name: ")
#     user_id = input("user_id: ") #for now authorization will be by uuid
#     message = input("request: ")
#     return {"message": message, "user_name": user_name, "user_id": user_id}

import socket
import json

class _NAMserver(object):
    bind = False
    nam_sock = None
    encoding = 'utf-8'

    @staticmethod
    def bind_socket():
        _NAMserver.nam_sock = socket.socket()
        _NAMserver.nam_sock.bind(('127.0.0.1', 9090))
        _NAMserver.nam_sock.listen(3)
        _NAMserver.bind = True

    @staticmethod
    def wait_for_conn():
        client_conn, client_addr = _NAMserver.nam_sock.accept()
        client_conn.settimeout(3)
        data = _NAMserver.get_data(client_conn, 1024)
        client_conn.settimeout(None)
        return {"client_addr": client_addr, "client_conn": client_conn, "data": data}

    @staticmethod
    def get_data(client_conn, bytes):
        return json.loads(client_conn.recv(bytes).decode())
    
    @staticmethod
    def send_data(client_conn, data):
        return client_conn.send(json.dumps(data).encode(encoding=_NAMserver.encoding))

def start_server():
    _NAMserver.bind_socket()

def wait_for_conn():
    return _NAMserver.wait_for_conn()

def get_data(client_conn, bytes):
    return _NAMserver.get_data(client_conn, bytes)

def send_data(client_conn, data):
    _NAMserver.send_data(client_conn, data)

# start_server()
# wait_for_new_conn()

# def get_data():
#     data = NAMserver.nam_conn.recv(1024)
#     return json.loads(data)

# def send_data(message, user_name):
#     NAMserver.nam_conn.send(bytes(f"new message for user {user_name}: {message}", encoding = 'UTF-8'))


# def send_response(message, user_name):
#     print(f"new reply for user {user_name}: {message}")

# def wait_for_req():
#     user_name = input("user_name: ")
#     user_id = input("user_id: ") #for now authorization will be by uuid
#     message = input("request: ")
#     return {"message": message, "user_name": user_name, "user_id": user_id}

import socket
import json

class _NAMserver(object):#basic serverside networking structure
    bind = False
    nam_sock = None
    ip = None
    port = None
    encoding = None
    clients_count = None

    @staticmethod
    def bind_socket(ip, port, encoding, clients_count): # create socket and bind to port
        _NAMserver.nam_sock = socket.socket()
        _NAMserver.nam_sock.bind((ip, port))
        _NAMserver.nam_sock.listen(clients_count)
        _NAMserver.nam_sock.settimeout(3)
        _NAMserver.ip = ip
        _NAMserver.port = port
        _NAMserver.encoding = encoding
        _NAMserver.clients_count = clients_count
        _NAMserver.bind = True

    @staticmethod
    def wait_for_conn(): # listen for incoming connections and auth data right after it
        if not _NAMserver.bind: return {"corrupted": "server was not inited"}
        try:
            client_conn, client_addr = _NAMserver.nam_sock.accept()
            client_conn.settimeout(3) #session's timeout for 3 second
            data = _NAMserver.get_data(client_conn, 1024)
            return {"client_addr": client_addr, "client_conn": client_conn, "auth_data": data["auth_data"], "settings": data["settings"]}
        except Exception as e:
            return None

    @staticmethod
    def get_data(client_conn, bytes):
        try:
            if not _NAMserver.bind: return {"corrupted": "server was not inited"}
            return json.loads(client_conn.recv(bytes).decode())
        except Exception as e:
            return None

    @staticmethod
    def send_data(client_conn, data):
        try:
            if not _NAMserver.bind: return
            client_conn.send(json.dumps(data).encode(encoding=_NAMserver.encoding))
        except Exception as e:
            return None

    @staticmethod
    def check_conn(client_conn, test_data):
        try:
            if not _NAMserver.bind: return
            client_conn.send(json.dumps(test_data).encode(encoding=_NAMserver.encoding))
        except ConnectionResetError:
            return False
        return True

    @staticmethod
    def close_conn(client_conn):
        if not _NAMserver.bind: return
        client_conn.close()

def start_server(params_dict):
    _NAMserver.bind_socket(params_dict["ip"], params_dict["port"], params_dict["encoding"], params_dict["clients_count"])

def wait_for_conn():
    return _NAMserver.wait_for_conn()

def close_conn(client_conn):
    _NAMserver.close_conn(client_conn)

def get_data(client_conn, bytes):
    return _NAMserver.get_data(client_conn, bytes)

def send_data(client_conn, data):
    _NAMserver.send_data(client_conn, data)

def check_if_alive(client_conn, test_data):
    return _NAMserver.check_conn(client_conn, test_data)

def get_encoding():
    return _NAMserver.encoding

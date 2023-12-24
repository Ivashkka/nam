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
        _NAMserver.ip = ip
        _NAMserver.port = port
        _NAMserver.encoding = encoding
        _NAMserver.clients_count = clients_count
        _NAMserver.bind = True

    @staticmethod
    def wait_for_conn(): # listen for incoming connections and auth data right after it
        if not _NAMserver.bind: return {"corrupted": "server was not inited"}
        client_conn, client_addr = _NAMserver.nam_sock.accept()
        client_conn.settimeout(3) #timeout of session for 3 second if no auth data received 
        data = _NAMserver.get_data(client_conn, 1024)
        client_conn.settimeout(None)
        return {"client_addr": client_addr, "client_conn": client_conn, "data": data}

    @staticmethod
    def get_data(client_conn, bytes):
        if not _NAMserver.bind: return {"corrupted": "server was not inited"}
        return json.loads(client_conn.recv(bytes).decode())
    
    @staticmethod
    def send_data(client_conn, data):
        if not _NAMserver.bind: return
        client_conn.send(json.dumps(data).encode(encoding=_NAMserver.encoding))

def start_server(params_dict):
    _NAMserver.bind_socket(params_dict["ip"], params_dict["port"], params_dict["encoding"], params_dict["clients_count"])

def wait_for_conn():
    return _NAMserver.wait_for_conn()

def get_data(client_conn, bytes):
    return _NAMserver.get_data(client_conn, bytes)

def send_data(client_conn, data):
    _NAMserver.send_data(client_conn, data)

def get_encoding():
    return _NAMserver.encoding

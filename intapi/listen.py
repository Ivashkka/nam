import socket
import json
import os

class _NAMserver(object):#basic serverside networking structure
    bind = False
    nam_sock = None
    local_sock = None
    uspath = None
    ip = None
    port = None
    encoding = None
    clients_count = None

    INTERACT = False #will change in future

    @staticmethod
    def bind_socket(ip, port, encoding, clients_count, unix_socket_path, interact): # create socket and bind to port
        _NAMserver.INTERACT = interact
        _NAMserver.nam_sock = socket.socket()
        _NAMserver.nam_sock.bind((ip, port))
        _NAMserver.nam_sock.listen(clients_count)
        _NAMserver.nam_sock.settimeout(3)
        if not _NAMserver.INTERACT:
            _NAMserver.uspath = unix_socket_path
            _NAMserver.close_local_sock()
            _NAMserver.local_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            _NAMserver.local_sock.bind(unix_socket_path)
            _NAMserver.local_sock.listen(1)
        _NAMserver.ip = ip
        _NAMserver.port = port
        _NAMserver.encoding = encoding
        _NAMserver.clients_count = clients_count
        _NAMserver.bind = True

    @staticmethod
    def wait_for_conn(): # listen for incoming connections and auth data right after it
        if not _NAMserver.bind: return None
        try:
            client_conn, client_addr = _NAMserver.nam_sock.accept()
            client_conn.settimeout(3) #session's timeout for 3 second
            data = _NAMserver.get_data(client_conn, 1024)
            return {"client_addr": client_addr, "client_conn": client_conn, "auth_data": data["auth_data"], "settings": data["settings"]}
        except Exception as e:
            return None

    @staticmethod
    def get_data(client_conn, bytes):
        if not _NAMserver.bind: return None
        try:
            return json.loads(client_conn.recv(bytes).decode())
        except Exception as e:
            return None

    @staticmethod
    def send_data(client_conn, data):
        if not _NAMserver.bind: return None
        try:
            client_conn.send(json.dumps(data).encode(encoding=_NAMserver.encoding))
        except Exception as e:
            return None

    @staticmethod
    def check_conn(client_conn, test_data):
        if not _NAMserver.bind: return None
        try:
            client_conn.send(json.dumps(test_data).encode(encoding=_NAMserver.encoding))
        except Exception as e:
            if e != socket.timeout: return False
        return True

    @staticmethod
    def close_conn(client_conn):
        if not _NAMserver.bind: return None
        client_conn.close()

    @staticmethod
    def get_ctl_connect():
        if not _NAMserver.bind: return None
        ctl_conn, ctl_address = _NAMserver.local_sock.accept()
        return ctl_conn

    @staticmethod
    def get_ctl_command(ctl_conn, bytes):
        if not _NAMserver.bind: return None
        try:
            return ctl_conn.recv(bytes).decode()
        except Exception as e:
            return None

    @staticmethod
    def send_ctl_answer(ctl_conn, data):
        if not _NAMserver.bind: return None
        try:
            ctl_conn.send(data.encode(encoding=_NAMserver.encoding))
        except Exception as e:
            return None

    def close_ctl_conn(ctl_conn):
        if not _NAMserver.bind: return None
        ctl_conn.close()

    @staticmethod
    def close_local_sock():
        if not _NAMserver.bind: return None
        try:
            os.unlink(_NAMserver.uspath)
        except Exception as e:
            if os.path.exists(_NAMserver.uspath):
                raise Exception(f"can't remove old {_NAMserver.uspath} socket!")

def start_server(params_dict, interact):
    _NAMserver.bind_socket(params_dict["ip"], params_dict["port"], params_dict["encoding"], params_dict["clients_count"], params_dict["unix_socket_path"], interact)

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

def close_local_sock():
    _NAMserver.close_local_sock()

def get_ctl_connect():
    return _NAMserver.get_ctl_connect()

def send_ctl_answer(ctl_conn, data):
    _NAMserver.send_ctl_answer(ctl_conn, data)

def get_ctl_command(ctl_conn, bytes):
    return _NAMserver.get_ctl_command(ctl_conn, bytes)

def close_ctl_conn():
    return _NAMserver.close_ctl_conn()

def get_encoding():
    return _NAMserver.encoding

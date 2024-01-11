########################## listen.py ##########################

import socket
import json
import enum
import os

class NAMconcode(enum.Enum): # execution codes
    Success     =   0
    Timeout     =   1
    Fail        =   2
    JsonFail    =   3
    OldSock     =   4

class _NAMserver(object): # basic serverside networking structure
    bind = False
    nam_sock = None
    local_sock = None
    uspath = None
    ip = None
    port = None
    encoding = None
    clients_count = None

    INTERACT = True

    @staticmethod
    def bind_socket(ip, port, encoding, clients_count, unix_socket_path, interact): # create socket and bind to port
        init_stages_codes = []
        _NAMserver.INTERACT = interact
        try:
            _NAMserver.nam_sock = socket.socket()
            _NAMserver.nam_sock.bind((ip, port))
            _NAMserver.nam_sock.listen(clients_count)
            _NAMserver.nam_sock.settimeout(3)
            init_stages_codes.append(NAMconcode.Success)
        except:
            print("failed to create network socket")
            init_stages_codes.append(NAMconcode.Fail)
        if not _NAMserver.INTERACT:
            _NAMserver.uspath = unix_socket_path
            init_stages_codes.append(_NAMserver.close_local_sock())
            try:
                _NAMserver.local_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                _NAMserver.local_sock.bind(unix_socket_path)
                _NAMserver.local_sock.listen(1)
                init_stages_codes.append(NAMconcode.Success)
            except:
                print("failed to bind unix named socket")
                init_stages_codes.append(NAMconcode.Fail)
        _NAMserver.ip = ip
        _NAMserver.port = port
        _NAMserver.encoding = encoding
        _NAMserver.clients_count = clients_count
        if NAMconcode.Fail not in init_stages_codes:
            _NAMserver.bind = True
            return NAMconcode.Success
        else: return NAMconcode.Fail

    @staticmethod
    def wait_for_conn(): # listen for incoming connections and auth data right after it
        if not _NAMserver.bind: return NAMconcode.Fail
        try:
            client_conn, client_addr = _NAMserver.nam_sock.accept()
            client_conn.settimeout(3) #session's timeout for 3 second
            data = _NAMserver.get_data(client_conn, 4096)
            if type(data) != NAMconcode:
                return {"client_addr": client_addr, "client_conn": client_conn, "auth_data": data["auth_data"], "settings": data["settings"]}
            else: return data
        except Exception as e:
            return NAMconcode.Fail

    @staticmethod
    def get_data(client_conn, bytes):
        if not _NAMserver.bind: return NAMconcode.Fail
        try:
            return json.loads(client_conn.recv(bytes).decode())
        except socket.timeout:
            return NAMconcode.Timeout
        except json.JSONDecodeError as e:
            return NAMconcode.JsonFail
        except Exception as e:
            return NAMconcode.Fail

    @staticmethod
    def send_data(client_conn, data):
        if not _NAMserver.bind: return NAMconcode.Fail
        try:
            client_conn.send(json.dumps(data).encode(encoding=_NAMserver.encoding))
            return NAMconcode.Success
        except socket.timeout:
            return NAMconcode.Timeout
        except:
            return NAMconcode.Fail

    @staticmethod
    def close_conn(client_conn): # close existing client connection
        if not _NAMserver.bind: return NAMconcode.Fail
        client_conn.close()
        client_conn = None
        return NAMconcode.Success

    @staticmethod
    def get_ctl_connect(): # get unix named socket connection
        if not _NAMserver.bind: return NAMconcode.Fail
        try:
            ctl_conn, ctl_address = _NAMserver.local_sock.accept()
            return ctl_conn
        except Exception as e:
            return NAMconcode.Fail

    @staticmethod
    def get_ctl_command(ctl_conn, bytes): # get unix named socket data
        if not _NAMserver.bind: return NAMconcode.Fail
        try:
            return ctl_conn.recv(bytes).decode()
        except socket.timeout:
            return NAMconcode.Timeout
        except:
            return NAMconcode.Fail

    @staticmethod
    def send_ctl_answer(ctl_conn, data): # send data to unix named socket
        if not _NAMserver.bind: return NAMconcode.Fail
        try:
            ctl_conn.send(data.encode(encoding=_NAMserver.encoding))
        except socket.timeout:
            return NAMconcode.Timeout
        except:
            return NAMconcode.Fail

    def close_ctl_conn(ctl_conn): # close connection over unix named socket
        if not _NAMserver.bind: return NAMconcode.Fail
        ctl_conn.close()
        return NAMconcode.Success

    @staticmethod
    def close_local_sock(): # close unix named socket
        if not _NAMserver.bind: return NAMconcode.Fail
        try:
            os.unlink(_NAMserver.uspath)
            return NAMconcode.Success
        except Exception as e:
            if os.path.exists(_NAMserver.uspath):
                print(f"can't remove old {_NAMserver.uspath} socket!")
                return NAMconcode.Fail

def start_server(params_dict, interact):
    return _NAMserver.bind_socket(params_dict["ip"], params_dict["port"], params_dict["encoding"], params_dict["clients_count"], params_dict["unix_socket_path"], interact)

def wait_for_conn():
    return _NAMserver.wait_for_conn()

def close_conn(client_conn):
    return _NAMserver.close_conn(client_conn)

def get_data(client_conn, bytes):
    return _NAMserver.get_data(client_conn, bytes)

def send_data(client_conn, data):
    return _NAMserver.send_data(client_conn, data)

def close_local_sock():
    return _NAMserver.close_local_sock()

def get_ctl_connect():
    return _NAMserver.get_ctl_connect()

def send_ctl_answer(ctl_conn, data):
    return _NAMserver.send_ctl_answer(ctl_conn, data)

def get_ctl_command(ctl_conn, bytes):
    return _NAMserver.get_ctl_command(ctl_conn, bytes)

def close_ctl_conn():
    return _NAMserver.close_ctl_conn()

def get_encoding():
    return _NAMserver.encoding

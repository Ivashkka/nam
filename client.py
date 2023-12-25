import socket
import json
import uuid
import datastruct
import bcrypt
from getpass import getpass
from dataload import dload

class _NAMclient(object): #basic clientside networking structure
    init = False
    client_sock = None
    encoding = None
    server_ip = None
    server_port = None

    @staticmethod
    def init_socket(server_ip, server_port, encoding): #create socket
        _NAMclient.client_sock = socket.socket()
        _NAMclient.server_ip = server_ip
        _NAMclient.server_port = server_port
        _NAMclient.encoding = encoding
        _NAMclient.init = True

    @staticmethod
    def connect_to_srv(auth_data): #connect to srv and send auth data
        if not _NAMclient.init: return
        _NAMclient.client_sock.connect((_NAMclient.server_ip, _NAMclient.server_port))
        _NAMclient.send_data(auth_data)

    @staticmethod
    def get_data(bytes):
        if not _NAMclient.init: return {"corrupted": "client was not inited"}
        return json.loads(_NAMclient.client_sock.recv(bytes).decode())
    
    @staticmethod
    def send_data(data):
        if not _NAMclient.init: return
        return _NAMclient.client_sock.send(json.dumps(data).encode(encoding=_NAMclient.encoding))

def main():
    salt = b'$2b$12$ET4oX.YJCrU9OX92KWW2Ku'
    client_conf = dload.load_yaml("conf.yaml")["nam_client"]
    _NAMclient.init_socket(client_conf["server_ip"], client_conf["server_port"], client_conf["encoding"])
    user_name = input("user_name: ")
    user_pass = getpass("user_pass: ").encode(encoding=_NAMclient.encoding)
    auth_data = datastruct.NAMuser(name=user_name, pass_hash=bcrypt.hashpw(user_pass, salt).decode(), uuid=None)
    _NAMclient.connect_to_srv(auth_data=datastruct.to_dict(auth_data))
    while True:
        message = datastruct.AIrequest(input("request: "), uuid.uuid4().hex)
        _NAMclient.send_data(datastruct.to_dict(message))
        response = datastruct.from_dict(_NAMclient.get_data(1024))
        print(response.message)

main()

import socket
import json
import uuid
import datastruct

class _NAMclient(object): #basic clientside networking structure
    init = False
    client_sock = None
    encoding = 'utf-8'
    server_ip = '127.0.0.1'
    server_port = 9090

    @staticmethod
    def init_socket(): #create socket
        _NAMclient.client_sock = socket.socket()
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
    _NAMclient.init_socket()
    user_name = input("user_name: ")
    user_id = input("user_id: ")
    auth_data = datastruct.NAMuser(user_name, user_id)
    _NAMclient.connect_to_srv(auth_data=datastruct.to_dict(auth_data))
    while True:
        message = datastruct.AIrequest(input("request: "), uuid.uuid4().hex)
        _NAMclient.send_data(datastruct.to_dict(message))
        response = datastruct.from_dict(_NAMclient.get_data(1024))
        print(response.message)

main()

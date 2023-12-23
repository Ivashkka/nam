import enum

class NAMDtype(enum.Enum): # ai data type
    request = 0
    response = 1
    auth_data = 2

#basic classes for user, response, request and session:

class NAMuser:
    __slots__ = ['type', 'name', 'uuid']
    def __init__(self=None, name=None, uuid=None, dict=None):
        self.type = NAMDtype.auth_data
        self.name = name
        self.uuid = uuid
        if dict: self.from_dict(dict)
    def to_dict(self):
        return {"type": self.type.value, "name": self.name, "uuid": self.uuid}
    def from_dict(self, dict):
        self.name = dict["name"]
        self.uuid = dict["uuid"]
        self.type = NAMDtype(dict["type"])

class AIrequest:
    __slots__ = ['message', 'uuid', 'type']
    def __init__(self=None, message=None, uuid=None, dict=None):
        self.message = message
        self.uuid = uuid
        self.type = NAMDtype.request
        if dict: self.from_dict(dict)
    def to_dict(self):
        return {"type": self.type.value, "message": self.message, "uuid": self.uuid}
    def from_dict(self, dict):
        self.message = dict["message"]
        self.uuid = dict["uuid"]
        self.type = NAMDtype(dict["type"])

class AIresponse:
    __slots__ = ['message', 'uuid', 'type']
    def __init__(self=None, message=None, uuid=None, dict=None):
        self.message = message
        self.uuid = uuid
        self.type = NAMDtype.response
        if dict: self.from_dict(dict)
    def to_dict(self):
        return {"type": self.type.value, "message": self.message, "uuid": self.uuid}
    def from_dict(self, dict):
        self.message = dict["message"]
        self.uuid = dict["uuid"]
        self.type = NAMDtype(dict["type"])

class NAMconnection:
    __slots__ = ['uuid', 'user', 'client_conn', 'client_addr']
    def __init__(self, uuid, user, client_conn, client_addr):
        self.uuid = uuid
        self.user = user
        self.client_addr = client_addr
        self.client_conn = client_conn

class NAMsession:
    __slots__ = ['uuid', 'client', 'thread', 'messages_history', 'text_history', '__weakref__']
    def __init__(self, uuid, client, thread):
        self.uuid = uuid
        self.client = client
        self.thread = thread
        self.messages_history = [] #list of objects of type message
        self.text_history = [] #list of dictionaries for g4f requests
    
    def add_message(self, message):
        self.messages_history.append(message)
        match message.type:
            case NAMDtype.request:
                self.text_history.append({"role": "user", "content": message.message})
            case NAMDtype.response:
                self.text_history.append({"role": "assistant", "content": message.message})
            case _:
                pass

    def get_username(self):
        return self.client.user.name
    
    def get_useruuid(self):
        return self.client.user.uuid

    def get_client_conn(self):
        return self.client.client_conn

import enum

class NAMDtype(enum.Enum): # primary key to transfer data between server and client
    AIrequest       =   "AIrequest"
    AIresponse      =   "AIresponse"
    NAMuser         =   "NAMuser"
    NAMSesSettings  =   "NAMSesSettings"

class AImodels(enum.Enum):
    GPT35turbo  =   "gpt_35_turbo"
    GPT35long   =   "gpt_35_long"
    GPT4        =   "gpt_4"
    GPT4turbo   =   "gpt_4_turbo"

#basic classes for user, response, request and session:

class NAMuser:
    __slots__ = ['type', 'name', 'pass_hash', 'uuid']
    def __init__(self, name=None, pass_hash=None, uuid=None):
        self.type = NAMDtype.NAMuser
        self.name = name
        self.pass_hash = pass_hash
        self.uuid = uuid

class AIrequest:
    __slots__ = ['message', 'uuid', 'type']
    def __init__(self, message=None, uuid=None):
        self.message = message
        self.uuid = uuid
        self.type = NAMDtype.AIrequest

class AIresponse:
    __slots__ = ['message', 'uuid', 'type']
    def __init__(self, message=None, uuid=None):
        self.message = message
        self.uuid = uuid
        self.type = NAMDtype.AIresponse

class NAMSesSettings:
    __slots__ = ['model', 'type']
    def __init__(self, model=None):
        self.model = model
        self.type = NAMDtype.NAMSesSettings

class NAMconnection:
    __slots__ = ['uuid', 'user', 'client_conn', 'client_addr']
    def __init__(self, uuid, user, client_conn, client_addr):
        self.uuid = uuid
        self.user = user
        self.client_addr = client_addr
        self.client_conn = client_conn

class NAMsession:
    __slots__ = ['uuid', 'client', 'settings', 'thread', 'messages_history', 'text_history', '__weakref__']
    count = 0
    def __init__(self, uuid, client, settings, thread):
        self.uuid = uuid
        self.client = client
        self.settings = settings
        self.thread = thread
        self.messages_history = [] #list of objects of type message
        self.text_history = [] #list of dictionaries for g4f requests
        NAMsession.count += 1

    def add_message(self, message):
        self.messages_history.append(message)
        match message.type:
            case NAMDtype.AIrequest:
                self.text_history.append({"role": "user", "content": message.message})
            case NAMDtype.AIresponse:
                self.text_history.append({"role": "assistant", "content": message.message})
            case _:
                pass

    def get_username(self):
        return self.client.user.name
    
    def get_useruuid(self):
        return self.client.user.uuid

    def get_client_conn(self):
        return self.client.client_conn


def to_dict(obj): #convert any class object to dictionary
    if not hasattr(obj, 'type'): return
    dict = {}
    for field in obj.__slots__:
        dict[field] = getattr(obj, field)
        if field == 'type' or field == 'model':
            dict[field] = getattr(obj, field).value
    return dict

def from_dict(dict): #create class object from given dictionary
    if not 'type' in dict: return
    obj = globals()[dict['type']]()
    for field in dict:
        setattr(obj, field, dict[field])
        if field == 'type':
            setattr(obj, field, NAMDtype(dict[field]))
        if field == 'model':
            setattr(obj, field, AImodels(dict[field]))
    return obj

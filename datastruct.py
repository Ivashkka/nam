import enum
import uuid as ud

class NAMDtype(enum.Enum): # primary key to transfer data between server and client
    AIrequest       =   "AIrequest"
    AIresponse      =   "AIresponse"
    NAMuser         =   "NAMuser"
    NAMSesSettings  =   "NAMSesSettings"
    NAMcommand      =   "NAMcommand"

class NAMCtype(enum.Enum):
    ContextReset    =   "ContextReset"
    TestConn        =   "TestConn"

class AImodels(enum.Enum):
    GPT35turbo  =   "gpt_35_turbo"
    GPT35long   =   "gpt_35_long"
    GPT4        =   "gpt_4"
    GPT4turbo   =   "gpt_4_turbo"

#basic classes for user, response, request and session:

class NAMuser:
    __slots__ = ['type', 'name', 'pass_hash', 'uuid']
    def __init__(self, name=None, pass_hash=None, uuid=ud.uuid4().hex):
        self.type = NAMDtype.NAMuser
        self.name = name
        self.pass_hash = pass_hash
        self.uuid = uuid

class AIrequest:
    __slots__ = ['message', 'uuid', 'type']
    def __init__(self, message=None, uuid=ud.uuid4().hex):
        self.message = message
        self.uuid = uuid
        self.type = NAMDtype.AIrequest

class AIresponse:
    __slots__ = ['message', 'uuid', 'type']
    def __init__(self, message=None, uuid=ud.uuid4().hex):
        self.message = message
        self.uuid = uuid
        self.type = NAMDtype.AIresponse

class NAMSesSettings:
    __slots__ = ['model', 'type']
    def __init__(self, model=None):
        self.model = model
        self.type = NAMDtype.NAMSesSettings

class NAMcommand:
    __slots__ = ['command', 'type']
    def __init__(self, command=None):
        self.command = command
        self.type = NAMDtype.NAMcommand

class NAMconnection:
    __slots__ = ['uuid', 'user', 'client_conn', 'client_addr']
    def __init__(self, user, client_conn, client_addr, uuid=ud.uuid4().hex):
        self.uuid = uuid
        self.user = user
        self.client_addr = client_addr
        self.client_conn = client_conn

class NAMsession:
    __slots__ = ['uuid', 'client', 'settings', 'thread', 'messages_history', '__weakref__']
    count = 0
    def __init__(self, client, settings, thread, uuid=ud.uuid4().hex):
        self.uuid = uuid
        self.client = client
        self.settings = settings
        self.thread = thread
        self.messages_history = [] #list of objects of type message
        NAMsession.count += 1

    def add_message(self, message):
        self.messages_history.append(message)

    def get_text_history(self):
        text_history = []
        for mes in self.messages_history:
            match mes.type:
                case NAMDtype.AIrequest:
                    text_history.append({"role": "user", "content": mes.message})
                case NAMDtype.AIresponse:
                    text_history.append({"role": "assistant", "content": mes.message})
                case _:
                    pass
        return text_history

    def reset_context(self):
        self.messages_history = []

    def get_username(self):
        return self.client.user.name
    
    def get_useruuid(self):
        return self.client.user.uuid

    def get_client_conn(self):
        return self.client.client_conn


def to_dict(obj, save_uuid=False): #convert any class object to dictionary
    if not hasattr(obj, 'type'): return None
    dict = {}
    for field in obj.__slots__:
        if field == 'uuid' and not save_uuid: continue
        if field == 'type' or field == 'model' or field == 'command':
            dict[field] = getattr(obj, field).value
            continue
        dict[field] = getattr(obj, field)
    return dict

def from_dict(dict): #create class object from given dictionary
    if dict == None or not 'type' in dict: return None
    obj = globals()[dict['type']]()
    for field in dict:
        if field == 'type':
            setattr(obj, field, NAMDtype(dict[field]))
            continue
        if field == 'model':
            setattr(obj, field, AImodels(dict[field]))
            continue
        if field == 'command':
            setattr(obj, field, NAMCtype(dict[field]))
            continue
        setattr(obj, field, dict[field])
    return obj

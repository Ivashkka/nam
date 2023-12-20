class NAMuser:
    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid

class AIrequest:
    def __init__(self, message, uuid):
        self.message = message
        self.uuid = uuid

class AIresponse:
    def __init__(self, message, uuid):
        self.message = message
        self.uuid = uuid

class NAMsession:
    def __init__(self, uuid, user, thread):
        self.uuid = uuid
        self.user = user
        self.thread = thread
        self.messages_history = []
        self.new_message_detected = False

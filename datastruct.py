import enum

class AIMtype(enum.Enum): # ai message type
    request = 0
    response = 1

#basic classes for user, response, request and session:

class NAMuser:
    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid

class AIrequest:
    def __init__(self, message, uuid):
        self.message = message
        self.uuid = uuid
        self.type = AIMtype.request

class AIresponse:
    def __init__(self, message, uuid):
        self.message = message
        self.uuid = uuid
        self.type = AIMtype.response

class NAMsession:
    def __init__(self, uuid, user, thread):
        self.uuid = uuid
        self.user = user
        self.thread = thread
        self.messages_history = [] #list of objects of type message
        self.text_history = [] #list of dictionaries for g4f requests
        self.new_message_detected = False #serves for conditions in session thread
    
    def add_message(self, message):
        self.messages_history.append(message)
        if (message.type == AIMtype.request):
            self.new_message_detected = True
            self.text_history.append({"role": "user", "content": message.message})
        else:
            self.text_history.append({"role": "assistant", "content": message.message})

    

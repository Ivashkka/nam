import uuid
import datastruct
import weakref
from intapi import listen
from threading import Thread
from aireq import ai

user_sessions = []

def open_new_session(client):
    ses_list_id = len(user_sessions) #will be used to access original session object in list
    ses = datastruct.NAMsession(uuid=uuid.uuid4().hex, client=client, thread=Thread(target=session_thread, args=[ses_list_id]))
    user_sessions.append(ses)
    user_sessions[ses_list_id].thread.start()
    return weakref.ref(user_sessions[ses_list_id])

def session_thread(session_id):
    ses_ref = weakref.ref(user_sessions[session_id])
    while True:
        data = listen.get_data(ses_ref().get_client_conn(), 1024)
        if (data["type"] == datastruct.NAMDtype.request.value):
            req = datastruct.AIrequest(dict=data)
            ses_ref().add_message(req)
            ai_resp = datastruct.AIresponse(message=ai.ask(ses_ref().text_history), uuid=uuid.uuid4().hex)
            ses_ref().add_message(ai_resp)
            listen.send_data(ses_ref().get_client_conn(), data=ai_resp.to_dict())

# def session_thread(session_id): ###weak point !! (TODO: find another way to store session data in thread)
#     ses_ref = weakref.ref(user_sessions[session_id]) #ref to the corresponding session object in list
#     while True:
#         if (ses_ref().new_message_detected):
#             ses_ref().new_message_detected = False #(could be moved into session add message method)
#             ai_resp = datastruct.AIresponse(message=ai.ask(ses_ref().text_history), uuid=uuid.uuid4()) #ask g4f
#             ses_ref().add_message(ai_resp) #add response to session history
#             listen.send_data(ai_resp.message, ses_ref().user.name) #send response to the corresponding user

# def main():
#     while True:
#         gotreq = listen.get_data() #wait for client request
#         user = datastruct.NAMuser(name=gotreq["user_name"], uuid=gotreq["user_id"])
#         message = datastruct.AIrequest(message=gotreq["message"], uuid=uuid.uuid4())
#         user_ses = None
#         for i in range(0, len(user_sessions)): #search for existing session for user
#             if (user_sessions[i].user.uuid == user.uuid):
#                 user_ses = weakref.ref(user_sessions[i])
#                 break
#         else: #create new if none was found
#             user_ses = open_new_session(user)
#         user_ses().add_message(message) #add new message to the found/created session

def main():
    while True:
        conn = listen.wait_for_conn()
        if (conn["data"]["type"] == datastruct.NAMDtype.auth_data.value):
            client_user = datastruct.NAMuser(dict=conn["data"])
            client = datastruct.NAMconnection(uuid.uuid4().hex, client_user, conn["client_conn"], conn["client_addr"])
            open_new_session(client=client)

if __name__ == "__main__":
    ai.initg4f()
    listen.start_server()
    main()

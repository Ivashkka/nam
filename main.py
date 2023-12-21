import uuid
import datastruct
import weakref
from intapi import listen
from threading import Thread
from aireq import ai

user_sessions = []

def open_new_session(user):
    ses_list_id = len(user_sessions) #will be used to access original session object in list
    ses = datastruct.NAMsession(uuid=uuid.uuid4(), user=user, thread=Thread(target=session_thread, args=[ses_list_id]))
    user_sessions.append(ses)
    user_sessions[ses_list_id].thread.start()
    return weakref.ref(user_sessions[ses_list_id])

def session_thread(session_id): ###weak point !! (TODO: find another way to store session data in thread)
    ses_ref = weakref.ref(user_sessions[session_id]) #ref to the corresponding session object in list
    while True:
        if (ses_ref().new_message_detected):
            ses_ref().new_message_detected = False #(could be moved into session add message method)
            ai_resp = datastruct.AIresponse(message=ai.ask(ses_ref().text_history), uuid=uuid.uuid4()) #ask g4f
            ses_ref().add_message(ai_resp) #add response to session history
            listen.send_response(ai_resp.message, ses_ref().user.name) #send response to the corresponding user

def main():
    while True:
        gotreq = listen.wait_for_req() #wait for client request
        user = datastruct.NAMuser(name=gotreq["user_name"], uuid=gotreq["user_id"])
        message = datastruct.AIrequest(message=gotreq["message"], uuid=uuid.uuid4())
        user_ses = None
        for i in range(0, len(user_sessions)): #search for existing session for user
            if (user_sessions[i].user.uuid == user.uuid):
                user_ses = weakref.ref(user_sessions[i])
                break
        else: #create new if none was found
            user_ses = open_new_session(user)
        user_ses().add_message(message) #add new message to the found/created session


if __name__ == "__main__":
    ai.initg4f()
    main()

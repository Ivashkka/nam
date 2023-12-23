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
    ses_ref = weakref.ref(user_sessions[session_id]) #ref to the corresponding session object in list
    while True:
        data = datastruct.from_dict(listen.get_data(ses_ref().get_client_conn(), 1024)) #get request
        if data.type == datastruct.NAMDtype.AIrequest:
            ses_ref().add_message(data) #add request to session history
            ai_resp = datastruct.AIresponse(message=ai.ask(ses_ref().text_history), uuid=uuid.uuid4().hex) #ask g4f
            ses_ref().add_message(ai_resp) #add response to session history
            listen.send_data(ses_ref().get_client_conn(), data=datastruct.to_dict(ai_resp)) #send response to the user

def main():
    while True:
        conn = listen.wait_for_conn()
        auth = datastruct.from_dict(conn["data"])
        if auth.type == datastruct.NAMDtype.NAMuser:
            client = datastruct.NAMconnection(uuid.uuid4().hex, auth, conn["client_conn"], conn["client_addr"]) # info about client
            open_new_session(client=client)

if __name__ == "__main__":
    ai.initg4f()
    listen.start_server()
    main()

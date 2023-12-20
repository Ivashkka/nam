import uuid
import datastruct
import weakref
from intapi import listen
from threading import Thread
from aireq import ai

user_sessions = []

def open_new_session(user):
    ses_list_id = len(user_sessions)
    ses = datastruct.NAMsession(uuid=uuid.uuid4(), user=user, thread=Thread(target=session_thread, args=[ses_list_id]))
    user_sessions.append(ses)
    user_sessions[ses_list_id].thread.start()
    return weakref.ref(user_sessions[ses_list_id])

def session_thread(session_id): ###weak point !! (TODO: find another way to store session data in thread)
    ses_ref = weakref.ref(user_sessions[session_id])
    while True:
        if (ses_ref().new_message_detected):
            ses_ref().new_message_detected = False
            ai_resp = datastruct.AIresponse(message=ai.ask(ses_ref().messages_history[-1].message), uuid=uuid.uuid4())
            ses_ref().messages_history.append(ai_resp)
            listen.send_response(ai_resp.message, ses_ref().user.name)


# def generate_request(message):
#     req = datastruct.AIrequest(message=message, uuid=uuid.uuid4())
#     ai.ask(req)


def main():
    while True:
        gotreq = listen.wait_for_req()
        user = datastruct.NAMuser(name=gotreq["user_name"], uuid=gotreq["user_id"])
        message = datastruct.AIrequest(message=gotreq["message"], uuid=uuid.uuid4())
        user_ses = None
        for i in range(0, len(user_sessions)):
            if (user_sessions[i].user.uuid == user.uuid):
                user_ses = weakref.ref(user_sessions[i])
                break
        else:
            user_ses = open_new_session(user)

        user_ses().messages_history.append(message)
        user_ses().new_message_detected = True


if __name__ == "__main__":
    ai.initg4f()
    main()

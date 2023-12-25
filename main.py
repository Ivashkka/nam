import uuid
import datastruct
import weakref
import bcrypt
from intapi import listen
from threading import Thread
from aireq import ai
from getpass import getpass
from dataload import dload

salt = b'$2b$12$ET4oX.YJCrU9OX92KWW2Ku'
server_manage_thread = None
known_users = []
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

def create_user():
    name = input("user name: ")
    passwd = getpass("password: ").encode(encoding=listen.get_encoding())
    usr = datastruct.NAMuser(uuid=uuid.uuid4().hex, name=name, pass_hash=bcrypt.hashpw(passwd, salt).decode())
    known_users.append(usr)

def show_info():
    print(f"sessions number: {datastruct.NAMsession.count}")
    print("all known useers:")
    for usr in known_users:
        print(f"name: {usr.name :<25} uuid:{usr.uuid :>25}")
    print("currently active users:")
    for ses in user_sessions:
        print(f"session uuid: {ses.uuid}\n\tname: {usr.name :<25} uuid:{usr.uuid :>25}")

def server_manage():
    while True:
        command = input("nam> ").split(" ")
        match command[0]:
            case "create":
                if len(command) < 2:
                    print("specify what to create or try help")
                    continue
                match command[1]:
                    case "user":
                        create_user()
                    case _:
                        print(f"wrong parameter '{command[1]}'")
            case "info":
                show_info()
            case "save":
                save_users()
            case "help":
                print("create user - create new user\nsave - save all users\ninfo - print all info\nhelp - show this info")
            case "":
                pass
            case _:
                print(f"wrong parameter '{command[0]}'")

def load_users():
    users_data = dload.load_json("users.json")
    for usr in users_data:
        known_users.append(datastruct.from_dict(usr))

def save_users():
    users_dictlist = []
    for usr in known_users:
        users_dictlist.append(datastruct.to_dict(usr))
    dload.save_json("users.json", users_dictlist)

def main():
    global server_manage_thread
    server_manage_thread=Thread(target=server_manage, args=[])
    server_manage_thread.start()
    while True:
        conn = listen.wait_for_conn()
        auth = datastruct.from_dict(conn["data"])
        if auth.type == datastruct.NAMDtype.NAMuser:
            for usr in known_users:
                if(usr.name == auth.name and usr.pass_hash == auth.pass_hash):
                    client = datastruct.NAMconnection(uuid.uuid4().hex, usr, conn["client_conn"], conn["client_addr"]) # info about client
                    open_new_session(client=client)
                    break

if __name__ == "__main__":
    ai.initg4f()
    server_conf = dload.load_yaml("conf.yaml")["nam_server"]
    listen.start_server(server_conf)
    load_users()
    main()

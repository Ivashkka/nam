import uuid
import datastruct
import weakref
import bcrypt
from intapi import listen
from threading import Thread
from aireq import ai
from getpass import getpass
from dataload import dload

class _NAMcore(object):
    salt = b'$2b$12$ET4oX.YJCrU9OX92KWW2Ku'
    known_users = []
    user_sessions = []
    server_manage_thread = None

    @staticmethod
    def start_core():
        ai.initg4f()
        _NAMcore.load_users()
        _NAMcore.start_listen_server()
        _NAMcore.server_manage_thread=Thread(target=_NAMcore.server_manage, args=[])
        _NAMcore.server_manage_thread.start()
        _NAMcore.serve_connections()

    @staticmethod
    def start_listen_server():
        server_conf = dload.load_yaml("conf.yaml")["nam_server"]
        listen.start_server(server_conf)
    
    @staticmethod
    def load_users():
        users_data = dload.load_json("users.json")
        for usr in users_data:
            _NAMcore.known_users.append(datastruct.from_dict(usr))

    @staticmethod
    def save_users():
        users_dictlist = []
        for usr in _NAMcore.known_users:
            users_dictlist.append(datastruct.to_dict(usr))
        dload.save_json("users.json", users_dictlist)

    @staticmethod
    def create_user():
        name = input("user name: ")
        passwd = getpass("password: ").encode(encoding=listen.get_encoding())
        usr = datastruct.NAMuser(uuid=uuid.uuid4().hex, name=name, pass_hash=bcrypt.hashpw(passwd, _NAMcore.salt).decode())
        _NAMcore.known_users.append(usr)

    @staticmethod
    def serve_connections():
        while True:
            conn = listen.wait_for_conn()
            auth = datastruct.from_dict(conn["auth_data"])
            sett = datastruct.from_dict(conn["settings"])
            if auth.type == datastruct.NAMDtype.NAMuser and sett.type == datastruct.NAMDtype.NAMSesSettings:
                for usr in _NAMcore.known_users:
                    if(usr.name == auth.name and usr.pass_hash == auth.pass_hash):
                        client = datastruct.NAMconnection(uuid.uuid4().hex, usr, conn["client_conn"], conn["client_addr"]) # info about client
                        _NAMcore.open_new_session(client=client, settings=sett)
                        break

    @staticmethod
    def open_new_session(client, settings):
        ses_list_id = len(_NAMcore.user_sessions) #will be used to access original session object in list
        ses = datastruct.NAMsession(uuid=uuid.uuid4().hex, client=client, settings=settings, thread=Thread(target=_NAMcore.session_thread, args=[ses_list_id]))
        _NAMcore.user_sessions.append(ses)
        _NAMcore.user_sessions[ses_list_id].thread.start()
        return weakref.ref(_NAMcore.user_sessions[ses_list_id])

    @staticmethod
    def session_thread(session_id):
        ses_ref = weakref.ref(_NAMcore.user_sessions[session_id]) #ref to the corresponding session object in list
        while True:
            data = datastruct.from_dict(listen.get_data(ses_ref().get_client_conn(), 1024)) #get request
            if data.type == datastruct.NAMDtype.AIrequest:
                ses_ref().add_message(data) #add request to session history
                ai_resp = datastruct.AIresponse(message=ai.ask(ses_ref().text_history, ses_ref().settings.model.value), uuid=uuid.uuid4().hex) #ask g4f
                ses_ref().add_message(ai_resp) #add response to session history
                listen.send_data(ses_ref().get_client_conn(), data=datastruct.to_dict(ai_resp)) #send response to the user

    @staticmethod
    def show_info():
        print(f"sessions number: {datastruct.NAMsession.count}")
        print("all known useers:")
        for usr in _NAMcore.known_users:
            print(f"name: {usr.name :<25} uuid:{usr.uuid :>25}")
        print("currently active sessions:")
        for ses in _NAMcore.user_sessions:
            print(f"session uuid: {ses.uuid}\n\tname: {ses.get_username() :<25} uuid:{ses.get_useruuid() :>25}")

    @staticmethod
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
                            _NAMcore.create_user()
                        case _:
                            print(f"wrong parameter '{command[1]}'")
                case "info":
                    _NAMcore.show_info()
                case "save":
                    _NAMcore.save_users()
                case "help":
                    print("create user - create new user\nsave - save all users\ninfo - print all info\nhelp - show this info")
                case "":
                    pass
                case _:
                    print(f"wrong parameter '{command[0]}'")

def main():
    _NAMcore.start_core()

if __name__ == "__main__":
    main()

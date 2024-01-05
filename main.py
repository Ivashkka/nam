import datastruct
import weakref
import bcrypt
from intapi import listen
from threading import Thread
from threading import Event
from aireq import ai
from getpass import getpass
from dataload import dload
import signal
import setproctitle

class _NAMcore(object):
    salt = b'$2b$12$ET4oX.YJCrU9OX92KWW2Ku'
    known_users = []
    user_sessions = []
    server_manage_thread = None
    stop_event = Event()

    INTERACT = True #will change in future

    @staticmethod
    def start_core():
        signal.signal(signal.SIGTERM, _NAMcore.sigterm_handler)
        setproctitle.setproctitle('nam_server_python')
        _NAMcore.init_ai()
        _NAMcore.load_users()
        _NAMcore.start_listen_server()
        _NAMcore.server_manage_thread=Thread(target=_NAMcore.server_manage, args=[])
        _NAMcore.server_manage_thread.start()
        _NAMcore.serve_connections()

    @staticmethod
    def sigterm_handler(signal, frame):
        print('Received SIGTERM. Exiting gracefully...')
        _NAMcore.stop_event.set()

    @staticmethod
    def init_ai():
        ai_g4f_conf = dload.load_yaml("conf.yaml")["ai_settings"]["g4f_settings"]
        ai.initg4f(ai_g4f_conf)

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
            users_dictlist.append(datastruct.to_dict(usr, save_uuid=True))
        dload.save_json("users.json", users_dictlist)

    @staticmethod
    def create_user():
        name = input("user name: ")
        passwd = getpass("password: ").encode(encoding=listen.get_encoding())
        usr = datastruct.NAMuser(name=name, pass_hash=bcrypt.hashpw(passwd, _NAMcore.salt).decode())
        _NAMcore.known_users.append(usr)

    @staticmethod
    def delete_user(deleted_user_name):
        for i in range(0, len(_NAMcore.known_users)):
            if(_NAMcore.known_users[i].name == deleted_user_name):
                _NAMcore.known_users.pop(i)
                break

    @staticmethod
    def serve_connections():
        while True:
            if _NAMcore.stop_event.is_set():
                for i in range(0, len(_NAMcore.user_sessions)):
                    _NAMcore.user_sessions[i].thread.join()
                    listen.close_conn(_NAMcore.user_sessions[i].client.client_conn)
                if not _NAMcore.INTERACT: listen.close_local_sock()
                print("done")
                break
            while _NAMcore.find_dead_ses():
                pass
            conn = listen.wait_for_conn()
            if conn == None:
                continue
            auth = datastruct.from_dict(conn["auth_data"])
            sett = datastruct.from_dict(conn["settings"])
            if auth.type == datastruct.NAMDtype.NAMuser and sett.type == datastruct.NAMDtype.NAMSesSettings:
                for usr in _NAMcore.known_users:
                    if(usr.name == auth.name and usr.pass_hash == auth.pass_hash):
                        client = datastruct.NAMconnection(usr, conn["client_conn"], conn["client_addr"]) # info about client
                        _NAMcore.open_new_session(client=client, settings=sett)
                        break

    @staticmethod
    def find_dead_ses():
        for i in range(0, len(_NAMcore.user_sessions)):
            if not _NAMcore.user_sessions[i].thread.is_alive():
                listen.close_conn(_NAMcore.user_sessions[i].client.client_conn)
                _NAMcore.user_sessions.pop(i)
                datastruct.NAMsession.count -= 1
                return True
        else:
            return False

    @staticmethod
    def open_new_session(client, settings):
        ses_list_id = len(_NAMcore.user_sessions) #will be used to access original session object in list
        ses = datastruct.NAMsession(client=client, settings=settings, thread=Thread(target=_NAMcore.session_thread, args=[ses_list_id]))
        _NAMcore.user_sessions.append(ses)
        _NAMcore.user_sessions[ses_list_id].thread.name = f"{_NAMcore.user_sessions[ses_list_id].uuid[0:6]}_session_thread"
        _NAMcore.user_sessions[ses_list_id].thread.start()
        return weakref.ref(_NAMcore.user_sessions[ses_list_id])

    @staticmethod
    def session_thread(session_id):
        ses_ref = weakref.ref(_NAMcore.user_sessions[session_id]) #ref to the corresponding session object in list
        aireq_thread = None
        while True:
            conn_alive = listen.check_if_alive(ses_ref().get_client_conn(), datastruct.to_dict(datastruct.NAMcommand(datastruct.NAMCtype.TestConn)))
            if _NAMcore.stop_event.is_set() or not conn_alive:
                if aireq_thread != None: aireq_thread.join()
                break
            data = datastruct.from_dict(listen.get_data(ses_ref().get_client_conn(), 4096)) #get request
            if data == None: continue
            if data.type == datastruct.NAMDtype.AIrequest:
                if aireq_thread != None and aireq_thread.is_alive():
                    wait_resp = datastruct.AIresponse(message="wait for the answer to the previous question")
                    listen.send_data(ses_ref().get_client_conn(), data=datastruct.to_dict(wait_resp))
                    continue
                aireq_thread = Thread(target=_NAMcore.get_ai_resp_thread, args=[ses_ref, data])
                aireq_thread.name = f"{ses_ref().uuid[0:6]}_child_thread"
                aireq_thread.start()
            elif data.type == datastruct.NAMDtype.NAMSesSettings:
                ses_ref().settings = data
            elif data.type == datastruct.NAMDtype.NAMcommand:
                if data.command == datastruct.NAMCtype.ContextReset:
                    if aireq_thread != None and aireq_thread.is_alive():
                        wait_resp = datastruct.AIresponse(message="wait for the answer to the previous question")
                        listen.send_data(ses_ref().get_client_conn(), data=datastruct.to_dict(wait_resp))
                    else:
                        ses_ref().reset_context()
                        ok_resp = datastruct.AIresponse(message="context deleted")
                        listen.send_data(ses_ref().get_client_conn(), data=datastruct.to_dict(ok_resp))

    def get_ai_resp_thread(ses_ref, req):
        ses_ref().add_message(req) #add request to session history
        ai_resp = datastruct.AIresponse(message=ai.ask(ses_ref().get_text_history(), ses_ref().settings.model.value)) #ask g4f
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
            if not _NAMcore.INTERACT:
                ctl_conn = listen.get_ctl_connect()
                command = listen.get_ctl_command(ctl_conn).split(" ")
            else:
                print("nam> ", end="")
                command = input().split(" ")
            answer = ""
            match command[0]:
                case "create":
                    if len(command) < 2:
                        answer = "specify what to create or try help"
                        continue
                    match command[1]:
                        case "user":
                            _NAMcore.create_user()
                        case _:
                            answer = f"wrong parameter '{command[1]}'"
                case "delete":
                    if len(command) < 3:
                        answer = "specify what to delete or try help"
                        continue
                    match command[1]:
                        case "user":
                            _NAMcore.delete_user(command[2])
                        case _:
                            answer = f"wrong parameter '{command[1]}'"
                case "info":
                    _NAMcore.show_info()
                case "status":
                    answer = f"running\nCurrent sessions - {datastruct.NAMsession.count}"
                case "save":
                    _NAMcore.save_users()
                case "stop":
                    print("nam server is stopping...")
                    _NAMcore.stop_event.set()
                    if not _NAMcore.INTERACT: listen.close_ctl_conn(ctl_conn)
                    break
                case "help":
                    answer = "create user - create new user\nsave - save all users\ninfo - print all info\nstatus - print short info\ndelete user <name> - delete user\nstop - stop server\nhelp - show this info"
                case "":
                    pass
                case _:
                    answer = f"wrong parameter '{command[0]}'"
            if not _NAMcore.INTERACT:
                listen.send_ctl_answer(ctl_conn, answer)
                listen.close_ctl_conn(ctl_conn)
            else:
                if answer != "": print(answer)

def main():
    _NAMcore.start_core()

if __name__ == "__main__":
    main()

######################################################################################
##                                                                                  ##
##                                  server core                                     ##
##                                                                                  ##
######################################################################################


#####   usage:

# server can be started in interact or backgroud mode
# interact mode occupies terminal and needed for tests
# background mode can be safely started with & and uses unix named sockets for communication with ctl instrument

# arguments: python3 main.py <interact/background> <configs_path>
# if no <interact/background> specified, the server starts in the interact mode
# if no <configs_path> specified, the server looking for configs in current folder

# to start server in interact mode use `python3 main.py interact .`
# to start server in background mode use `python3 main.py background <conf_path>`

# to execute any command try `command` for ex: `help`


#####   server insides:

# all work with sockets delegated to intapi/listen.py
# all work with files delegated to dataload/dload.py
# all datastructures used in core located in datastruct.py

# conf_keys dict used to check conf.yaml correctness
# commads_dict used to execute related to server commands functions by their name
# for ex: to add command `show something` to server, you need to add "show something":"show_something"
# to commads_dict, where show_something is actual name of _NAMcore function

# _NAMcore uses NAMEtype (NAM execution type) enum to take care of functions execute codes.
# there are other execution codes for other modules, like intapi/listen.py
# they are converted into NAMEtype in related functions

# _NAMcore uses NAMDtype as primary unit of transferring data

# Every session has it's own thread running with target function _NAMcore.session_thread
# If there are problems with client connection, session_thread stops and session object is deleted later in main loop
# server_manage_thread is thread to serve ctl user input

# stop_event to stop server

import datastruct
import bcrypt
from intapi import listen
from threading import Thread
from threading import Event
from aireq import ai
from dataload import dload
import signal
import setproctitle
import time
import sys
import inspect
import queue

class _NAMcore(object):
    salt                =   b'$2b$12$ET4oX.YJCrU9OX92KWW2Ku'
    conf_yaml           =   "conf.yaml"
    users_json          =   "users.json"
    known_users         =   []
    user_sessions       =   []
    current_output_ctl_conn = None
    ctl_output_queue = queue.Queue()

    stop_event              =   Event()
    server_manage_thread    =   None

    # list used to check conf.yaml correctness
    conf_keys = ["nam_server", "ip", "port", "encoding", "clients_count", "unix_socket_path", "ai_settings", "g4f_settings", "providers"]

    # dict for matching command and corresponding _NAMcore function
    commads_dict = {"create user":"create_user", "delete user":"delete_user", "info":"show_info",
                    "status":"show_status", "save":"save_users", "stop":"stop_all", "help":"show_help"}

    INTERACT = True # interact or background mode


########################## System functions ##########################

    @staticmethod
    def start_core():
        signal.signal(signal.SIGTERM, _NAMcore.sigterm_handler)   # handle SIGTERM signal
        setproctitle.setproctitle('nam_server_python')
        if _NAMcore.solve_cli_args() == datastruct.NAMEtype.IntFail: raise Exception("Wrong arguments or argument positions!")
        if _NAMcore.test_conf_file(_NAMcore.conf_yaml, _NAMcore.conf_keys) == False:
            raise Exception("conf.yaml file is invalid!")
        if _NAMcore.init_ai() == datastruct.NAMEtype.InitAiFail: raise Exception("Failed to init g4f! Maybe bad g4f_settings in conf.yaml")
        if _NAMcore.load_users() == datastruct.NAMEtype.IntFail: raise Exception("Failed to open or find users.json!")
        if _NAMcore.start_listen_server()  == datastruct.NAMEtype.InitListenFail: raise Exception("Failed to bind network socket!")
        _NAMcore.server_manage_thread=Thread(target=_NAMcore.server_manage, args=[])
        _NAMcore.server_manage_thread.start()
        _NAMcore.serve_connections()

    @staticmethod
    def solve_cli_args():
        if "interact" in sys.argv and "background" in sys.argv:
            return datastruct.NAMEtype.IntFail
        if "interact" in sys.argv:
            _NAMcore.INTERACT = True
        if "background" in sys.argv:
            _NAMcore.INTERACT = False
        if len(sys.argv) == 2:
            if str(sys.argv[1]) != "interact" and str(sys.argv[1]) != "background":
                if dload.test_file(str(sys.argv[1])+"/conf.yaml"):
                    _NAMcore.conf_yaml = str(sys.argv[1])+"/conf.yaml"
                    _NAMcore.users_json = str(sys.argv[1])+"/users.json"
                    return datastruct.NAMEtype.Success
        elif len(sys.argv) == 3:
            if str(sys.argv[2]) != "interact" and str(sys.argv[2]) != "background":
                if dload.test_file(str(sys.argv[2])+"/conf.yaml"):
                    _NAMcore.conf_yaml = str(sys.argv[2])+"/conf.yaml"
                    _NAMcore.users_json = str(sys.argv[2])+"/users.json"
                    return datastruct.NAMEtype.Success
        return datastruct.NAMEtype.IntFail


    @staticmethod
    def check_key(dictionary : dict, key): # check if key in multidimensional dictionary
        for dict_key in dictionary:
            if dict_key == key:
                return True
            if isinstance(dictionary[dict_key], dict):
                if _NAMcore.check_key(dictionary[dict_key], key):
                    return True
        return False

    @staticmethod
    def test_conf_file(path, args : list):
        if not dload.test_file(path): return False
        conf_dict = dload.load_yaml(path)
        all_keys_codes = []
        for arg in args:
            all_keys_codes.append(_NAMcore.check_key(conf_dict, arg))
        if False not in all_keys_codes:
            return True
        else : return False

    @staticmethod
    def send_output(data): # send output to ctl user depending on running mode (print if interact and unix named socket if bg)
        if data == None or data == "": return datastruct.NAMEtype.IntFail
        if _NAMcore.INTERACT == True:
            print(data)
            return datastruct.NAMEtype.Success
        elif _NAMcore.current_output_ctl_conn != None:
            sendcode = listen.send_ctl_answer(_NAMcore.current_output_ctl_conn, "")
            match sendcode:
                case listen.NAMconcode.Timeout:
                    _NAMcore.ctl_output_queue.put(data)
                    return datastruct.NAMEtype.ConTimeOut
                case listen.NAMconcode.Fail:
                    _NAMcore.ctl_output_queue.put(data)
                    return datastruct.NAMEtype.IntConFail
            while not _NAMcore.ctl_output_queue.empty():
                qdata = _NAMcore.ctl_output_queue.get()
                if "END" not in qdata or "IEN" not in qdata:
                    listen.send_ctl_answer(_NAMcore.current_output_ctl_conn, qdata+"\n")
            listen.send_ctl_answer(_NAMcore.current_output_ctl_conn, data+"\n")
            return datastruct.NAMEtype.Success
        else:
            _NAMcore.ctl_output_queue.put(data)
            return datastruct.NAMEtype.IntFail

    @staticmethod
    def get_input(prompt = "nam> "):  # get input from ctl user depending on running mode (input if interact and unix named socket if bg)
        if prompt == None: return datastruct.NAMEtype.IntFail
        if _NAMcore.INTERACT == True:
            print(prompt, end="")
            usr_input = input()
            return usr_input
        elif _NAMcore.current_output_ctl_conn != None:
            sendcode = _NAMcore.send_output(f"IEN {prompt}")
            if sendcode != datastruct.NAMEtype.Success: return sendcode
            usr_input = listen.get_ctl_command(_NAMcore.current_output_ctl_conn, 4096)
            match usr_input:
                case listen.NAMconcode.Timeout:
                    return datastruct.NAMEtype.ConTimeOut
                case listen.NAMconcode.Fail:
                    return datastruct.NAMEtype.IntConFail
                case "":
                    return datastruct.NAMEtype.IntFail
                case _:
                    return usr_input
        else: return datastruct.NAMEtype.IntFail

    @staticmethod
    def send_client_data(client_conn, data): # send data to nam client
        if datastruct.to_dict(data) == None: return datastruct.NAMEtype.IntFail
        sendcode = listen.send_data(client_conn, datastruct.to_dict(data))
        match sendcode:
            case listen.NAMconcode.Timeout:
                return datastruct.NAMEtype.ConTimeOut
            case listen.NAMconcode.Fail:
                return datastruct.NAMEtype.ClientConFail
            case listen.NAMconcode.Success:
                return datastruct.NAMEtype.Success

    @staticmethod
    def get_client_data(client_conn, nothing_extra=False): # get data from nam client
        data = listen.get_data(client_conn, 4096)
        if type(data) != listen.NAMconcode:
            obj = datastruct.from_dict(data)
            if obj != None:
                if obj.type == datastruct.NAMDtype.NAMexcode:
                    match obj.code:
                        case datastruct.NAMEtype.Success:
                            return datastruct.NAMEtype.Success
                        case datastruct.NAMEtype.SrvFail:
                            return datastruct.NAMEtype.IntFail
                        case _:
                            return datastruct.NAMEtype.ClientFail
                elif obj.type == datastruct.NAMDtype.NAMcommand:
                    if obj.command == datastruct.NAMCtype.TestConn and nothing_extra:
                        return _NAMcore.get_client_data(client_conn, nothing_extra)
                    else: return obj
                else: return obj
            else: return datastruct.NAMEtype.ClientFail
        match data:
            case listen.NAMconcode.Timeout:
                return datastruct.NAMEtype.ConTimeOut
            case listen.NAMconcode.Fail:
                return datastruct.NAMEtype.ClientConFail
            case listen.NAMconcode.JsonFail:
                return datastruct.NAMEtype.ClientFail

    @staticmethod
    def connection_is_alive(client_conn): # check if connection to client is alive (this is not used yet)
        excode = _NAMcore.send_client_data(client_conn, datastruct.NAMcommand(datastruct.NAMCtype.TestConn))
        if excode == datastruct.NAMEtype.ClientConFail:
            return False
        return True

    @staticmethod
    def sigterm_handler(signal, frame):
        print('Received SIGTERM. Exiting gracefully...')
        _NAMcore.stop_event.set()

    @staticmethod
    def init_ai():
        ai_g4f_conf = dload.load_yaml(_NAMcore.conf_yaml)["ai_settings"]["g4f_settings"]
        if type(ai_g4f_conf["providers"]) is not list or len(ai_g4f_conf["providers"]) < 1:
            return datastruct.NAMEtype.InitAiFail
        if ai.initg4f(ai_g4f_conf) == ai.AIexcode.Success:
            return datastruct.NAMEtype.Success
        else: return datastruct.NAMEtype.InitAiFail

    @staticmethod
    def start_listen_server():
        server_conf = dload.load_yaml(_NAMcore.conf_yaml)["nam_server"]
        excode = listen.start_server(server_conf, _NAMcore.INTERACT)
        if excode != listen.NAMconcode.Success: return datastruct.NAMEtype.InitListenFail
        else: return datastruct.NAMEtype.Success

    @staticmethod
    def load_users():
        users_data = dload.load_json(_NAMcore.users_json)
        if users_data == None: return datastruct.NAMEtype.IntFail
        for usr in users_data:
            usr_obj = datastruct.from_dict(usr)
            if usr_obj != None:
                _NAMcore.known_users.append(usr_obj)
        return datastruct.NAMEtype.Success

    @staticmethod
    def encode_passwd(passwd):
        return bcrypt.hashpw(passwd, _NAMcore.salt).decode()

    @staticmethod
    def get_new_client_conn():
        conn_dict_keys = ["auth_data", "settings", "client_conn", "client_addr"]
        conn = listen.wait_for_conn()
        match conn:
            case listen.NAMconcode.Timeout:
                return datastruct.NAMEtype.ConTimeOut, None
            case listen.NAMconcode.Fail:
                return datastruct.NAMEtype.ClientConFail, None
            case listen.NAMconcode.JsonFail:
                return datastruct.NAMEtype.ClientFail, None
        for conn_key in conn_dict_keys:
            if _NAMcore.check_key(conn, conn_key) == False: return datastruct.NAMEtype.IntFail, None
        if datastruct.from_dict(conn["auth_data"]) == None:
            return datastruct.NAMEtype.ClientFail, conn
        if datastruct.from_dict(conn["settings"]) == None:
            return datastruct.NAMEtype.ClientFail, conn
        return datastruct.NAMEtype.Success, conn

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
        ses_list_id = len(_NAMcore.user_sessions) # will be used to access original session object in list
        ses = datastruct.NAMsession(client=client, settings=settings, thread=Thread(target=_NAMcore.session_thread, args=[ses_list_id]))
        _NAMcore.user_sessions.append(ses)
        _NAMcore.user_sessions[ses_list_id].thread.name = f"{_NAMcore.user_sessions[ses_list_id].uuid[0:6]}_session_thread"
        _NAMcore.user_sessions[ses_list_id].thread.start()
        while not _NAMcore.user_sessions[ses_list_id].thread.is_alive(): # wait for the thread to start
            pass
        return datastruct.NAMEtype.Success


########################## Threads and main loop ##########################

    @staticmethod
    def serve_connections(): # main loop
        while True:
            if _NAMcore.stop_event.is_set():
                for usr_ses in _NAMcore.user_sessions:
                    usr_ses.thread.join()
                    listen.close_conn(usr_ses.client.client_conn)
                _NAMcore.server_manage_thread.join()
                if not _NAMcore.INTERACT: listen.close_local_sock()
                print("done")
                break
            while _NAMcore.find_dead_ses():
                pass
            excode, conn = _NAMcore.get_new_client_conn()
            if excode == datastruct.NAMEtype.ClientFail:
                err_resp = datastruct.NAMexcode(datastruct.NAMEtype.ClientFail)
                _NAMcore.send_client_data(conn["client_conn"], err_resp) # send response to the user
                listen.close_conn(conn["client_conn"])
                continue
            if excode != datastruct.NAMEtype.Success: continue
            auth = datastruct.from_dict(conn["auth_data"])
            sett = datastruct.from_dict(conn["settings"])
            if auth.type == datastruct.NAMDtype.NAMuser and sett.type == datastruct.NAMDtype.NAMSesSettings:
                for usr in _NAMcore.known_users:
                    if(usr.name == auth.name and usr.pass_hash == auth.pass_hash):
                        client = datastruct.NAMconnection(usr, conn["client_conn"], conn["client_addr"]) # info about client
                        ok_resp = datastruct.NAMexcode(datastruct.NAMEtype.Success)
                        send_code = _NAMcore.send_client_data(conn["client_conn"], ok_resp) # send response to the user
                        if send_code != datastruct.NAMEtype.Success:
                            listen.close_conn(conn["client_conn"])
                            break
                        time.sleep(0.5)
                        _NAMcore.open_new_session(client=client, settings=sett)
                        break
                else:
                    den_resp = datastruct.NAMexcode(datastruct.NAMEtype.Deny)
                    _NAMcore.send_client_data(conn["client_conn"], den_resp)
                    listen.close_conn(conn["client_conn"])
            else:
                err_resp = datastruct.NAMexcode(datastruct.NAMEtype.ClientFail)
                _NAMcore.send_client_data(conn["client_conn"], err_resp)
                listen.close_conn(conn["client_conn"])

    @staticmethod
    def session_thread(session_id):
        ses = _NAMcore.user_sessions[session_id] # session object in list
        aireq_thread = None
        conn_alive = True
        while True:
            if _NAMcore.stop_event.is_set() or not conn_alive:
                if aireq_thread != None: aireq_thread.join()
                break
            data = _NAMcore.get_client_data(ses.get_client_conn(), nothing_extra=True)
            if data == datastruct.NAMEtype.ClientConFail: conn_alive = False
            if type(data) == datastruct.NAMEtype:
                if data == datastruct.NAMEtype.ClientFail:
                    err_resp = datastruct.NAMexcode(datastruct.NAMEtype.ClientFail)
                    _NAMcore.send_client_data(ses.get_client_conn(), err_resp)
                continue

            if data.type == datastruct.NAMDtype.AIrequest: # serve ai request
                if aireq_thread != None and aireq_thread.is_alive():
                    wait_resp = datastruct.AIresponse(message="wait for the answer to the previous question")
                    _NAMcore.send_client_data(ses.get_client_conn(), wait_resp)
                    continue
                aireq_thread = Thread(target=_NAMcore.get_ai_resp_thread, args=[ses, data])
                aireq_thread.name = f"{ses.uuid[0:6]}_child_thread"
                aireq_thread.start()  # async wait for ai response
            elif data.type == datastruct.NAMDtype.NAMSesSettings: # change session settings
                ses.settings = data
                ok_resp = datastruct.NAMexcode(datastruct.NAMEtype.Success)
                _NAMcore.send_client_data(ses.get_client_conn(), ok_resp)
            elif data.type == datastruct.NAMDtype.NAMcommand: # serve commands
                if data.command == datastruct.NAMCtype.ContextReset:
                    if aireq_thread != None and aireq_thread.is_alive():
                        wait_resp = datastruct.AIresponse(message="wait for the answer to the previous question")
                        _NAMcore.send_client_data(ses.get_client_conn(), wait_resp)
                        continue
                    ses.reset_context()
                    ok_resp = datastruct.NAMexcode(datastruct.NAMEtype.Success)
                    _NAMcore.send_client_data(ses.get_client_conn(), ok_resp)
            else:
                err_resp = datastruct.NAMexcode(datastruct.NAMEtype.ClientFail)
                _NAMcore.send_client_data(ses.get_client_conn(), err_resp)
            time.sleep(1)

    def get_ai_resp_thread(ses, req): # wait for ai response thread
        ses.add_message(req) #add request to session history
        ai_resp = datastruct.AIresponse(message=ai.ask(ses.get_text_history(), ses.settings.model.value)) #ask g4f
        if ai_resp != ai.AIexcode.Fail:
            ses.add_message(ai_resp) #add response to session history
            _NAMcore.send_client_data(ses.get_client_conn(), ai_resp) #send response to the user
        else:
            err_resp = datastruct.NAMexcode(datastruct.NAMEtype.IntFail)
            _NAMcore.send_client_data(ses.get_client_conn(), err_resp)

    @staticmethod
    def server_manage(): # serve ctl user inputs
        while True:
            if _NAMcore.stop_event.is_set(): break
            if _NAMcore.INTERACT:
                if _NAMcore.direct_interaction() != datastruct.NAMEtype.Success:
                    _NAMcore.send_output("Error. The command was not executed")
            else:
                _NAMcore.current_output_ctl_conn = listen.get_ctl_connect()
                if type(_NAMcore.current_output_ctl_conn) == listen.NAMconcode:
                    _NAMcore.current_output_ctl_conn = None
                    continue
                if _NAMcore.ctl_interaction() != datastruct.NAMEtype.Success:
                    _NAMcore.send_output("Error. The command was not executed")
                _NAMcore.send_output("END")
                listen.close_ctl_conn(_NAMcore.current_output_ctl_conn)
                _NAMcore.current_output_ctl_conn = None


########################## Serve inputed command ##########################

    @staticmethod
    def direct_interaction():
        command = _NAMcore.get_input()
        if type(command) == datastruct.NAMEtype: return command
        return _NAMcore.serve_command(command)

    @staticmethod
    def ctl_interaction():
        command = _NAMcore.get_input()
        if type(command) == datastruct.NAMEtype: return command
        return _NAMcore.serve_command(command)

    @staticmethod
    def serve_command(command_string):
        if command_string == "": return datastruct.NAMEtype.Success
        command, args = _NAMcore.split_command(command_string)
        if command == None:
            _NAMcore.send_output("Wrong command, try help")
            return datastruct.NAMEtype.IntFail
        ctl_command_func = getattr(_NAMcore, _NAMcore.commads_dict[command])
        if len(inspect.signature(ctl_command_func).parameters) > 0:
            if args == None: return datastruct.NAMEtype.IntFail
            return ctl_command_func(args)
        else:
            if args != None: return datastruct.NAMEtype.IntFail
            return ctl_command_func()

    @staticmethod
    def split_command(command):
        command_list = list(filter(None, command.split(" ")))
        com, arg = None, None
        if len(command_list) < 1: return None, None
        if command_list[0] in _NAMcore.commads_dict: com = command_list[0]
        if " ".join(command_list[0:2]) in _NAMcore.commads_dict: com = " ".join(command_list[0:2])
        if com == None: return None, None
        if len(command_list) > len(com.split(" ")): arg = " ".join(command_list[len(com.split(" ")):])
        return com, arg


########################## Server commands implementations ##########################

    @staticmethod
    def show_info():
        _NAMcore.send_output(f"sessions number: {datastruct.NAMsession.count}")
        _NAMcore.send_output("all known useers:")
        for usr in _NAMcore.known_users:
            _NAMcore.send_output(f"name: {usr.name :<25} uuid:{usr.uuid :>25}")
        _NAMcore.send_output("currently active sessions:")
        for ses in _NAMcore.user_sessions:
            _NAMcore.send_output(f"session uuid: {ses.uuid}\n\tname: {ses.get_username() :<25} uuid:{ses.get_useruuid() :>25}")
        return datastruct.NAMEtype.Success

    @staticmethod
    def show_status():
        _NAMcore.send_output(f"running\nCurrent sessions - {datastruct.NAMsession.count}")
        return datastruct.NAMEtype.Success

    @staticmethod
    def show_help():
        _NAMcore.send_output("""
create user - create new user
save - save all users
info - print all info
status - print short info
delete user - delete user
stop - stop server
help - show this info""")
        return datastruct.NAMEtype.Success

    @staticmethod
    def stop_all():
        _NAMcore.send_output("nam server is stopping...")
        _NAMcore.stop_event.set()
        return datastruct.NAMEtype.Success

    @staticmethod
    def save_users():
        users_dictlist = []
        for usr in _NAMcore.known_users:
            users_dictlist.append(datastruct.to_dict(usr, save_uuid=True))
        save_code = dload.save_json(_NAMcore.users_json, users_dictlist)
        if save_code: return datastruct.NAMEtype.Success
        else: return datastruct.NAMEtype.IntFail

    @staticmethod
    def create_user():
        _NAMcore.send_output("all known users:")
        for usr in _NAMcore.known_users:
            _NAMcore.send_output(f"name: {usr.name :<25} uuid:{usr.uuid :>25}")
        _NAMcore.send_output("enter user data to create new one:")
        name = _NAMcore.get_input("user name (x to cancel): ")
        if name == "x": return datastruct.NAMEtype.Success
        passwd = _NAMcore.get_input("password (x to cancel): ")
        if passwd == "x": return datastruct.NAMEtype.Success
        if type(name) == datastruct.NAMEtype:
            return name
        if type(passwd) == datastruct.NAMEtype:
            return passwd
        _NAMcore.send_output("to save users, try 'save' or 'help' for more info")
        usr = datastruct.NAMuser(name=name, pass_hash=_NAMcore.encode_passwd(passwd.encode(encoding=listen.get_encoding())))
        _NAMcore.known_users.append(usr)
        return datastruct.NAMEtype.Success

    @staticmethod
    def delete_user():
        _NAMcore.send_output("all known users:")
        for usr in _NAMcore.known_users:
            _NAMcore.send_output(f"name: {usr.name :<25} uuid:{usr.uuid :>25}")
        deleted_user_name = _NAMcore.get_input("enter user name to delete: ")
        if type(deleted_user_name) == datastruct.NAMEtype: return deleted_user_name
        for i in range(0, len(_NAMcore.known_users)):
            if(_NAMcore.known_users[i].name == deleted_user_name):
                _NAMcore.known_users.pop(i)
                return datastruct.NAMEtype.Success
        _NAMcore.send_output("no such user")
        return datastruct.NAMEtype.IntFail



def main():
    _NAMcore.start_core()
    exit(0)

if __name__ == "__main__":
    main()

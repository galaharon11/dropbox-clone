import socket
import threading
from random import randint
from Queue import Queue
import os
from shutil import rmtree

import FTPDataOperations
import FTPDatabaseOperations
import FTPExceptions


class FTPServer(threading.Thread):
    def add_session_id(self, user_id):
        # Session id should be as random as possible, and it should be a long integer (at least 128 bit),
        # so hackers wont be able to brute force it.
        session_id = randint(0xFFFFFFFFFFFFFFFF, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        while session_id in self.sessions_id_to_user.keys():
            session_id = randint(0xFFFFFFFFFFFFFFFF, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

        self.sessions_id_to_user[session_id] = user_id
        return session_id

    def get_user_id(self, string):
        if 'SESSIONID=' not in string:
            raise FTPExceptions.NeedSessionID

        # May throw ValueError, that will trrigger 501 error code (Syntax error in parameters or arguments)
        session_id = int(string[string.find('SESSIONID=') + 10:])
        if session_id in self.sessions_id_to_user.keys():
            return self.sessions_id_to_user[session_id]
        else:
            raise FTPExceptions.InvalidSessionID


    def handle_ftp_data(self, command_queue, complition_queue):
        # Asks OS for a random port
        get_random_port_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        get_random_port_socket.bind(('', 0))
        get_random_port_socket.listen(1)
        # Make port reuable, because OS may delay the socket closing.
        get_random_port_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        data_port = get_random_port_socket.getsockname()[1]
        get_random_port_socket.close()

        complition_queue.put_nowait('227 PORT {0}'.format(data_port))

        # Create data socket. The data socket will trasfer the files, while the control socket (port 21)
        # will trasfer and recieve commands.
        data_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_server_socket.bind((self.ip, data_port))
        data_server_socket.listen(1)
        data_socket, client_addr = data_server_socket.accept()

        fucntions = {'APPE': FTPDataOperations.append_file,
                     'GET' : FTPDataOperations.get_file,
                     'LIST': FTPDataOperations.list_files}

        while True:
            while command_queue.empty():
                pass

            command = command_queue.get_nowait()
            operation =  fucntions[command[:command.find(' ')]]
            user_id = int(command[command.find('USERID=') + 7:])
            params = command[command.find(' ') + 1: command.find(' USERID=')].split(' ')
            try:
                succes_code = operation(params, user_id, self.path_to_files, data_socket, self.server_db)
                complition_queue.put_nowait(succes_code)
            except FTPExceptions as e:
                complition_queue.put_nowait(str(e))

    def handle_ftp_control(self, clientsock):
        '''
            Implemnts an FTP passive protocol
        '''
        command_queue, complition_queue = None, None
        accept_data_commands = False
        while True:
            try:
                command = clientsock.recv(1024)
                print command
                if command == 'PASV':
                    # Create a command queue to 'share' data between control thread (this thread) to the data thread
                    command_queue = Queue()
                    # Create a complition queue so control thread will know when the data thread finished
                    # handling a request
                    complition_queue = Queue()
                    data_thread = threading.Thread(target=self.handle_ftp_data,
                                                   args=(command_queue, complition_queue))
                    data_thread.deamon = True
                    data_thread.start()
                    while complition_queue.empty():
                        pass
                    clientsock.send(complition_queue.get_nowait())

                    accept_data_commands = True
                    continue
                else:
                    user_id = self.get_user_id(command)

                if (command.startswith('APPE') or command.startswith('GET')) and accept_data_commands:
                    # APPE syntax: APPE file_path_on_server SESSION=sessionid
                    # GET syntax: GET file_path_on_server group SESSION=sessionid
                    # if group is specified with GET, GET will ignore file_path_on_server

                    command_queue.put_nowait(command[:command.find('SESSIONID=')] + 'USERID=' + str(user_id))

                    while complition_queue.empty():
                        pass
                    clientsock.send(complition_queue.get_nowait())

                elif command.startswith('LIST') and accept_data_commands:
                    # LIST command will list every file in dir_path. group is optional parameter and it indicates
                    # that the server should list files shared by this group. group parameter can be specified
                    # to "SHARED", this will tell the server to include files associated with the user, that
                    # he is not their owner (the files shared with the user)
                    # LIST stntax: LIST dir_path group(optional) SESSION=sessionid
                    command_queue.put_nowait(command[:command.find('SESSIONID=')] + 'USERID=' + str(user_id))
                    while complition_queue.empty():
                        pass
                    clientsock.send(complition_queue.get_nowait())

                elif command.startswith('MKD'):
                    # MKD stntax: MKD dir_path SESSION=sessionid
                    relative_path = command[command.find('MKD ') + 4: command.find(' SESSIONID=')]
                    abs_path = os.path.join(self.path_to_files, str(user_id), relative_path[1:])
                    if os.path.exists(abs_path):
                        clientsock.send(str(FTPExceptions.FileAlreadyExists))
                    else:
                        os.mkdir(abs_path)
                        clientsock.send('212 Directory created.')

                elif command.startswith('RMD'):
                    # RMD stntax: RMD dir_path SESSION=sessionid
                    relative_path = command[command.find('RMD ') + 4: command.find(' SESSIONID=')]
                    abs_path = os.path.join(self.path_to_files, str(user_id), relative_path[1:])
                    if os.path.exists(abs_path):
                        for directory in os.walk(abs_path, topdown=False):  # Iterate directory recursively
                            for file_path in directory[2]:
                                abs_file_path = os.path.join(directory[0], file_path)
                                self.remove_file_from_db(abs_file_path, user_id)

                        rmtree(abs_path)  # delete directory recursively
                        clientsock.send('212 Directory deleted.')
                    else:
                        clientsock.send('550 Directory was not found.')

                elif command.startswith('DELE'):
                    # DELE stntax: DELE file_name SESSION=sessionid
                    relative_path = command[command.find('DELE ') + 5: command.find(' SESSIONID=')]
                    abs_path = os.path.join(self.path_to_files, str(user_id), relative_path[1:])
                    if os.path.exists(abs_path):
                        FTPDatabaseOperations.remove_file_from_db(abs_path, user_id)
                        os.remove(abs_path)
                        clientsock.send('213 File deleted.')
                    else:
                        clientsock.send('550 File was not found.')

                elif command.startswith('RNTO'):
                    # On standart ftp servers, to rename a file the client must enter RNFR command
                    # and RNTO command right after it. On this implementation, the client need to
                    # enter only RNTO command with 2 parameters.
                    # RNTO syntax: RNTO path_to_file path_to_new_file SESSION=sessionid
                    # Example: RNTO \a\b\before.txt \a\b\after.txt
                    relative_path, new_path = command[command.find('RNTO ') + 5: command.find(' SESSIONID=')].split(' ')
                    abs_path = os.path.join(self.path_to_files, str(user_id), relative_path[1:])
                    new_abs_path = os.path.join(self.path_to_files, str(user_id), new_path[1:])
                    if os.path.exists(abs_path) and not os.path.exists(new_abs_path):
                        FTPDatabaseOperations.change_file_path_on_db(self.server_db, abs_path, new_abs_path)
                        os.rename(abs_path, new_abs_path)
                        clientsock.send('213 File name changed.')
                    else:
                        clientsock.send('550 File is not found.') # FIXME: different error codes

                elif command.startswith('SHAR'):
                    # This command is not a valid ftp command. It will tell the server to share a specific file with
                    # other user, specified by user_name param.
                    # RNTO syntax: RNTO path_to_file user_name SESSION=sessionid
                    # Example: RNTO \a\text.txt user123
                    relative_path, user_name = command[command.find('SHAR ') + 5: command.find(' SESSIONID=')].split(' ')
                    abs_path = os.path.join(self.path_to_files, str(user_id), relative_path[1:])
                    if os.path.exists(abs_path):
                        if FTPDatabaseOperations.add_user_to_file_db(self.server_db, abs_path, user_name):
                            clientsock.send('213 File shared successfully.')
                        else:
                            raise FTPExceptions.InternalError
                    else:
                        raise FTPExceptions.FileDoesNotExists
                else:
                    print command
                    raise FTPExceptions.NotImplemented

                accept_data_commands = False

            except (FTPExceptions.FTPException) as e:
                clientsock.send(str(e))
            except (ValueError):
                clientsock.send('501 Syntax error in parameters or arguments')
            except socket.error as e:
                if e.errno == 10054:
                    return

    def handle_new_control_connection(self):
        while True:
            clientsock, addr = self.control_socket.accept()
            client_control_thread = threading.Thread(target=self.handle_ftp_control, args=(clientsock,))
            client_control_thread.daemon = True
            client_control_thread.start()

    def __init__(self, server_ip, server_db):
        threading.Thread.__init__(self, target=self.handle_new_control_connection, args=())
        self.daemon = True

        self.ip = server_ip
        self.server_db = server_db

        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 21 is ftp contorl port
        self.control_socket.bind((self.ip, 21))
        self.control_socket.listen(5)

        # Will map a session's id to user's id in the database
        self.sessions_id_to_user = {}

        self.path_to_files = os.path.join(os.path.dirname(__file__), 'files')
        if not os.path.exists(self.path_to_files):
            os.mkdir(self.path_to_files)

        self.start()

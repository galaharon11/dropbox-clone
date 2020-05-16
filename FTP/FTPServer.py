import socket
import threading
from random import randint
from Queue import Queue
import os

import FTPDataOperations
import FTPControlOperations
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


    def handle_ftp_data(self, command_queue, completion_queue):
        # Asks OS for a random port
        get_random_port_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        get_random_port_socket.bind(('', 0))
        get_random_port_socket.listen(1)
        # Make port reuable, because OS may delay the socket closing.
        get_random_port_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        data_port = get_random_port_socket.getsockname()[1]
        get_random_port_socket.close()

        completion_queue.put_nowait('227 PORT {0}'.format(data_port))

        # Create data socket. The data socket will trasfer the files, while the control socket (port 21)
        # will trasfer and recieve commands.
        data_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_server_socket.bind((self.ip, data_port))
        data_server_socket.listen(1)
        data_socket, client_addr = data_server_socket.accept()

        data_fucntions = {'APPE': FTPDataOperations.append_file,
                          'GET' : FTPDataOperations.get_file,
                          'LIST': FTPDataOperations.list_files }

        while True:
            while command_queue.empty():
                pass

            command = command_queue.get_nowait()
            print command
            operation = data_fucntions[command[:command.find(' ')]]
            user_id = int(command[command.find('USERID=') + 7:])
            params = command[command.find(' ') + 1: command.find(' USERID=')].split(' ')
            try:
                print params
                succes_code = operation(params, user_id, self.path_to_files, data_socket, self.server_db)
                completion_queue.put_nowait(succes_code)
            except FTPExceptions.FTPException as e:
                print str(e)
                completion_queue.put_nowait(str(e))

    def handle_ftp_control(self, clientsock):
        """
        Implemnts an FTP passive protocol
        """
        # Create a command queue to 'share' data between control thread (this thread) to the data thread
        command_queue = Queue()
        # Create a complition queue so control thread will know when the data thread finished
        # handling a request
        completion_queue = Queue()

        control_fucntions = {'APPE': FTPControlOperations.append_file,
                             'GET' : FTPControlOperations.get_file,
                             'LIST': FTPControlOperations.list_files,
                             'MKD' : FTPControlOperations.mkdir,
                             'RMD' : FTPControlOperations.rmdir,
                             'DELE': FTPControlOperations.delete_file,
                             'RNTO': FTPControlOperations.rename_file,
                             'SHAR': FTPControlOperations.share_file,
                             'GROUP': FTPControlOperations.group_operations }

        while True:
            try:
                command = clientsock.recv(1024)
                print command
                if command == 'PASV':
                    data_thread = threading.Thread(target=self.handle_ftp_data,
                                                   args=(command_queue, completion_queue))
                    data_thread.deamon = True
                    data_thread.start()
                    while completion_queue.empty():
                        pass

                    clientsock.send(completion_queue.get_nowait())
                    continue

                # Check if the server has the user's files firectory, create it if not
                user_id = self.get_user_id(command)
                dir_path = os.path.join(self.path_to_files, str(user_id))
                if not os.path.exists(dir_path):
                    os.mkdir(dir_path)

                operation = control_fucntions[command[:command.find(' ')]]
                params = command[command.find(' ') + 1: command.find(' SESSIONID=')].split(' ')
                operation(params, user_id, self.path_to_files, self.server_db, command_queue, completion_queue)

                while completion_queue.empty():
                    pass

                clientsock.send(completion_queue.get_nowait())

            except FTPExceptions.FTPException as e:
                print 'catched:', str(e)
                clientsock.send(str(e))

            except KeyError:
                clientsock.send('502 not implemented')

            except ValueError:
                clientsock.send('501 Syntax error in parameters or arguments')

            except socket.error as e:
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
        self.path_to_files = 'files'
        if not os.path.exists(self.path_to_files):
            os.mkdir(self.path_to_files)

        self.start()

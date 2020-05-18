import socket
import threading
from random import randint
from Queue import Queue
import os
import traceback

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
            operation = data_fucntions[command[:command.find(' ')]]
            user_id = int(command[command.find('USERID=') + 7:])
            params = command[command.find(' ') + 1: command.find(' USERID=')].split(' ')
            try:
                succes_code = operation(params, user_id, self.path_to_files, data_socket, self.server_db)
                completion_queue.put_nowait(succes_code)

                if operation == FTPDataOperations.get_file:
                    self.logger.add_file_log('User {0} downloaded file in path {1}.', user_id, params[0])
                elif operation == FTPDataOperations.append_file:
                    self.logger.add_file_log('User {0} uploaded file to path {1}.', user_id, params[0])

            except FTPExceptions.FTPException as e:
                try:
                    # user_id may be invalid
                    self.logger.add_error_log(str(e) + ". User: {0}.", user_id)
                except NameError:
                    pass
                completion_queue.put_nowait(str(e))

    def handle_ftp_control(self, control_sock):
        """
        Implemnts an FTP passive protocol.
        """
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
                command = control_sock.recv(1024).decode('utf8')
                if command == 'PASV':
                    # Create a command queue to 'share' data between control thread (this thread) to the data thread
                    command_queue = Queue()
                    # Create a complition queue so control thread will know when the data thread finished
                    # handling a request
                    completion_queue = Queue()

                    data_thread = threading.Thread(target=self.handle_ftp_data,
                                                   args=(command_queue, completion_queue))
                    data_thread.deamon = True
                    data_thread.start()
                    while completion_queue.empty():
                        pass

                    control_sock.send(completion_queue.get_nowait())
                    continue

                # Check if the server has the user's files firectory, create it if not
                user_id = self.get_user_id(command)
                dir_path = os.path.join(self.path_to_files, str(user_id))
                if not os.path.exists(dir_path):
                    os.mkdir(dir_path)

                operation = control_fucntions[command[:command.find(' ')]]
                params = command[command.find(' ') + 1: command.find(' SESSIONID=')].split(' ')
                operation(params, user_id, self.path_to_files, self.server_db, command_queue, completion_queue)

                if operation == FTPControlOperations.group_operations:
                    if params[0] == 'CREATE':
                        self.logger.add_group_log('Group {0} created.', params[1])
                    if params[0] == 'DELETE':
                        self.logger.add_group_log('Group {0} deleted.', params[1])

                while completion_queue.empty():
                    pass

                control_sock.send(completion_queue.get_nowait())
            except FTPExceptions.FTPException as e:
                try:
                    # user_id may be invalid
                    self.logger.add_error_log(str(e) + '. User: {0}.', user_id)
                except NameError:
                    pass
                control_sock.send(str(e))

            except KeyError:
                control_sock.send('502 not implemented')

            except ValueError:
                control_sock.send('501 Syntax error in parameters or arguments')

            except socket.error as e:
                return

    def handle_new_control_connection(self):
        while True:
            control_sock, addr = self.control_socket.accept()
            client_control_thread = threading.Thread(target=self.handle_ftp_control, args=(control_sock,))
            client_control_thread.daemon = True
            client_control_thread.start()

    def __init__(self, server_ip, server_db, logger):
        threading.Thread.__init__(self, target=self.handle_new_control_connection, args=())
        self.daemon = True

        self.ip = server_ip
        self.server_db = server_db

        self.logger = logger

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

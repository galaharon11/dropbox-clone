import socket
import threading
from random import randint
from Queue import Queue
import os
import traceback
from shutil import rmtree

import FTPDataOperations
import FTPExceptions


class FTPServer(threading.Thread):
    def send_file(self, data_socket, file_path, user_id, group=''):
        file = None
        try:
            if group == 'SHARED':
                files_shared_with_user = self.get_all_files_associated_with_user(user_id,
                                        permission_filter=1, reverse_filter=True)
                for shared_file in files_shared_with_user:
                    if os.path.basename(file_path) == os.path.basename(shared_file):
                        abs_file_path = shared_file
            else:
                dir_path = os.path.join(self.path_to_files, str(user_id))
                abs_file_path = os.path.join(dir_path, file_path)

            if not group:
                if not os.path.exists(dir_path):
                    raise IOError

            print abs_file_path
            if not group:
                if not self.check_permissions(abs_file_path, user_id): # FIXME: change to real permissions
                    raise FTPExceptions.PermissionDenied

            file = open(abs_file_path, 'rb')
            while True:
                file_data = file.read()
                if file_data:
                    data_socket.send(file_data)
                else:
                    file.close()
                    data_socket.close()
                    return abs_file_path

        except IOError:
            print "IOERROR"
            file.close()
            data_socket.close()
            return ''

    def recieve_file(self, data_socket, file_path, user_id):
        # TODO: Check if file name already in server, and alert client
        file = None
        try:
            dir_path = os.path.join(self.path_to_files, str(user_id))
            if not os.path.exists(dir_path):
                os.mkdir(dir_path)

            abs_path = os.path.join(dir_path, file_path)
            if os.path.exists(abs_path):
                raise FTPExceptions.FileAlreadyExists

            file = open(abs_path, 'wb')
            while True:
                file_data = data_socket.recv(1024)
                if file_data:
                    file.write(file_data)
                else:
                    file.close()
                    data_socket.close()
                    return abs_path

        except IOError:
            print "IOERROR"
            file.close()
            data_socket.close()
            return ''

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

    def change_file_path_on_db(self, file_path, new_file_path, permissions=1):
        cursor = self.server_db.cursor()
        cursor.execute('''UPDATE files SET file_path=? WHERE file_path=?''', (new_file_path, file_path))
        self.server_db.commit()

    def add_user_to_file_db(self, file_path, user_name, permissions=0):
        cursor = self.server_db.cursor()
        cursor.execute('''SELECT file_id FROM files WHERE file_path=?''', (file_path,))
        file_id = int(cursor.fetchone()[0])
        cursor.execute('''SELECT user_id FROM users WHERE username=?''', (user_name,))
        user_id = int(cursor.fetchone()[0])
        cursor.execute('''INSERT INTO users_files VALUES (?, ?, ?)''', (user_id, file_id, permissions))
        self.server_db.commit()

    def add_file_to_db(self, file_path, user_id, is_dir=False, permissions=1):
        cursor = self.server_db.cursor()
        cursor.execute('''INSERT INTO files VALUES (null, ?, ?)''', (file_path, is_dir))
        self.server_db.commit()
        cursor.execute('''SELECT file_id FROM files WHERE file_path=?''', (file_path,))
        file_id = int(cursor.fetchone()[0])
        cursor.execute('''INSERT INTO users_files VALUES (? , ?, ?)''', (user_id, file_id, permissions))
        self.server_db.commit()

    def remove_file_from_db(self, file_path, user_id, is_dir=False, permissions=1):
        cursor = self.server_db.cursor()
        cursor.execute('''SELECT file_id FROM files WHERE file_path=?''', (file_path,))
        file_id = int(cursor.fetchone()[0])
        cursor.execute('''DELETE FROM users_files WHERE file_id=?''', (file_id,))
        cursor.execute('''DELETE FROM files WHERE file_id=?''', (file_id,))
        self.server_db.commit()

    def get_all_files_associated_with_user(self, user_id, permission_filter=0, reverse_filter=False):
        '''
        Get all files associated with user specified by user_id. if permission_filter is non-zero,
        the function will filter files with the specific permission specified. If reverse_filter is True,
        the function will return every file that associated with the user that does not contain permission_filter
        for the user.
        '''
        cursor = self.server_db.cursor()
        cursor.execute('''SELECT file_id, permissions FROM users_files WHERE user_id=?''', (user_id,))
        queries = set(cursor.fetchall())
        if permission_filter:
            filtered = set(filter(lambda query: query[1] == permission_filter, queries))
            queries = queries - filtered if reverse_filter else queries

        file_ids = [str(q[0]) for q in queries]
        cursor.execute('''SELECT file_path FROM files WHERE file_id IN (?)''', (','.join(file_ids),))

        return [query[0] for query in cursor.fetchall()]


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

       # fucntions = {'APPE': FTPDataOperations.append_file,
        #             'GET' : FTPDataOperations.get_file,
         #            'LIST': FTPDataOperations.list_files,
         #            'APPE': FTPDataOperations.append_file}


        while True:
            while command_queue.empty():
                pass

            abs_file_path = ''
            command = command_queue.get_nowait()
            user_id = int(command[command.find('USERID=') + 7:])
            if command.startswith('APPE') or command.startswith('GET'):
                if command.startswith('APPE'):
                    file_path = command[command.find('APPE ') + 5: command.find(' USERID=')]
                    try:
                        abs_file_path = self.recieve_file(data_socket, file_path, str(user_id))
                        if abs_file_path:
                            self.add_file_to_db(abs_file_path, str(user_id), permissions=1)
                    except FTPExceptions.FileAlreadyExists as e:
                        print e
                        complition_queue.put_nowait(str(e))

                elif command.startswith('GET'):
                    params = command[command.find('GET ') + 4: command.find(' USERID=')]
                    if ' ' in params:
                        file_path, group = params.split(' ')
                    else:
                        file_path, group = params, ''
                    abs_file_path = self.send_file(data_socket, file_path, user_id, group=group)

                if abs_file_path:
                    complition_queue.put_nowait("226 Trasfer complete.")
                else:
                    complition_queue.put_nowait("500 Internal Error.")  # just a placeholder

            elif command.startswith('LIST'):
                params = command[command.find('LIST ') + 5: command.find(' USERID=')]
                if params.count(' ') == 1:
                    relative_path, group = params.split(' ')
                else:
                    relative_path = params
                    group = ''

                abs_path = os.path.join(self.path_to_files, str(user_id), relative_path[1:])
                if not os.path.exists(abs_path):
                    if relative_path=='\\':
                        os.mkdir(abs_path)
                    else:
                        complition_queue.put_nowait("550 Directory was not found.")

                if not group:
                    files_and_dirs_on_dir = map(lambda file_name: os.path.join(abs_path, file_name), os.listdir(abs_path))
                else:
                    files_and_dirs_on_dir = self.get_all_files_associated_with_user(user_id,
                                                 permission_filter=1, reverse_filter=True)

                dirs_on_dir = filter(lambda dir_path: os.path.isdir(dir_path), files_and_dirs_on_dir)
                files_on_dir = filter(lambda file_path: not os.path.isdir(file_path), files_and_dirs_on_dir)
                dirs_on_dir = map(lambda dir: os.path.basename(dir), dirs_on_dir)
                files_on_dir = map(lambda file: os.path.basename(file), files_on_dir)

                data_socket.send(';;;'.join([','.join(files_on_dir), ','.join(dirs_on_dir)]))
                complition_queue.put_nowait("212 Directory sent Ok.")

    def check_permissions(self, file_path, user_id, permissions=1):  # just owner for now, will need to change this
        cursor = self.server_db.cursor()
        cursor.execute('''SELECT file_id FROM files WHERE file_path=?''', (file_path,))
        file_id = int(cursor.fetchone()[0])
        cursor.execute('''SELECT user_id, permissions FROM users_files WHERE file_id=?''', (file_id,))
        user_id_from_db, permissions_from_db = cursor.fetchone()
        # Return true if permissions and user_id match, will need to change this to support permissions
        return(int(user_id_from_db) == user_id and int(permissions_from_db) == permissions)

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
                        self.remove_file_from_db(abs_path, user_id)
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
                        self.change_file_path_on_db(abs_path, new_abs_path)
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
                        self.add_user_to_file_db(abs_path, user_name)
                        clientsock.send('213 File shared successfully.')
                    else:
                        clientsock.send('550 File is not found.') # FIXME: different error codes
                else:
                    print command
                    raise FTPExceptions.NotImplemented

                accept_data_commands = False

            except (FTPExceptions.FTPException) as e:
                traceback.print_exc()
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

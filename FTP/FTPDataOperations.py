import os

import FTPExceptions
import FTPDatabaseOperations


def recieve_file(abs_file_path, data_socket):
    # TODO: Check if file name already in server, and alert client
    file = None
    try:
        print abs_file_path
        if os.path.exists(abs_file_path):
            raise FTPExceptions.FileAlreadyExists

        file = open(abs_file_path, 'wb')
        while True:
            file_data = data_socket.recv(1024)
            if file_data:
                file.write(file_data)
            else:
                file.close()
                data_socket.close()
                return abs_file_path

    except IOError:
        file.close()
        data_socket.close()
        raise FTPExceptions.InternalError


def send_file(abs_file_path, data_socket):
    file = None
    try:
        print abs_file_path
        if not os.path.exists(abs_file_path):
            raise IOError

        file = open(abs_file_path, 'rb')
        while True:
            file_data = file.read()
            print 'packet'
            if file_data:
                data_socket.send(file_data)
            else:
                print 'closing file'
                file.close()
                data_socket.close()
                return abs_file_path

    except IOError:
        file.close()
        raise FTPExceptions.InternalError


def append_file(params, user_id, path_to_files, data_socket, database):
    if len(params) == 2:
        file_path, group = params
    else:
        file_path, group = params[0], ''

    abs_file_path = recieve_file(file_path, data_socket)
    if abs_file_path:
        FTPDatabaseOperations.add_file_to_db(database, abs_file_path, str(user_id), permissions=1)

    if not abs_file_path:
        raise FTPExceptions.InternalError
    return "226 Trasfer complete."


def get_file(params, user_id, path_to_files, data_socket, database):
    if len(params) == 2:
        file_path, group = params
    else:
        file_path, group = params[0], ''

    data_socket.send(str(os.stat(file_path).st_size))
    print file_path
    abs_file_path = send_file(file_path, data_socket)
    if not abs_file_path:
        raise FTPExceptions.InternalError
    return "226 Trasfer complete."


def list_files(params, user_id, path_to_files, data_socket, database):
    if len(params) == 2:
        relative_path, group = params
    else:
        relative_path, group = params[0], ''

    abs_path = os.path.join(path_to_files, str(user_id), relative_path[1:])
    if not os.path.exists(abs_path):
        if relative_path=='\\' and not group:
            os.mkdir(abs_path)
        else:
            raise FTPExceptions.FileDoesNotExists

    if not group:
        files_and_dirs_on_dir = map(lambda file_name: os.path.join(abs_path, file_name), os.listdir(abs_path))
    elif group=='SHARED':
        files_and_dirs_on_dir = FTPDatabaseOperations.get_all_files_associated_with_user(database,
                                user_id, permission_filter=1, reverse_filter=True)

    dirs_on_dir = filter(lambda dir_path: os.path.isdir(dir_path), files_and_dirs_on_dir)
    files_on_dir = filter(lambda file_path: not os.path.isdir(file_path), files_and_dirs_on_dir)
    dirs_on_dir = map(lambda dir: os.path.basename(dir), dirs_on_dir)
    files_on_dir = map(lambda file: os.path.basename(file), files_on_dir)

    data_socket.send(';;;'.join([','.join(files_on_dir), ','.join(dirs_on_dir)]))
    return "212 Directory sent Ok."

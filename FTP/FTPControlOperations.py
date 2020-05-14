import os
from shutil import rmtree

import FTPExceptions
import FTPDatabaseOperations


def append_file(params, user_id, path_to_files, server_db, command_queue, compilation_queue):
    """
    Add a file to the FTP server.
    command syntax: APPE file_path_on_server SESSION=sessionid

    """

    command_queue.put_nowait(' '.join(['APPE'] + params + ['USERID=' + str(user_id)]))


def get_file(params, user_id, path_to_files, server_db, command_queue, compilation_queue):
    """
    Get a file from FTP server. if group is specified with GET, GET will get
    a file associated to a the specied group.
    command syntax: GET file_path_on_server group SESSION=sessionid
    """

    command_queue.put_nowait(' '.join(['GET'] + params + ['USERID=' + str(user_id)]))


def list_files(params, user_id, path_to_files, server_db, command_queue, compilation_queue):
    """
    LIST command will list every file in dir_path. group is optional parameter and it indicates
    that the server should list files shared by this group. group parameter can be specified
    to "SHARED", this will tell the server to include files associated with the user, that
    he is not their owner (the files shared with the user)
    LIST stntax: LIST dir_path group(optional) SESSION=sessionid
    """
    print ' '.join(['LIST'] + params + ['USERID=' + str(user_id)])
    command_queue.put_nowait(' '.join(['LIST'] + params + ['USERID=' + str(user_id)]))


def delete_file(params, user_id, path_to_files, server_db, command_queue, compilation_queue):
    """
    Delete a file on server.
    DELE stntax: DELE file_name SESSION=sessionid
    """
    relative_path = params[0]
    abs_path = os.path.join(path_to_files, str(user_id), relative_path[1:])
    if os.path.exists(abs_path):
        FTPDatabaseOperations.remove_file_from_db(server_db, abs_path, user_id)
        os.remove(abs_path)
        compilation_queue.put_nowait('213 File deleted.')
    else:
        raise FTPExceptions.FileDoesNotExists


def rename_file(params, user_id, path_to_files, server_db, command_queue, compilation_queue):
    """
    On standart ftp servers, to rename a file the client must enter RNFR command
    and RNTO command right after it. On this implementation, the client need to
    enter only RNTO command with 2 parameters.
    RNTO syntax: RNTO path_to_file path_to_new_file SESSION=sessionid
    Example: RNTO \a\b\before.txt \a\b\after.txt
    """
    relative_path, new_path = params
    abs_path = os.path.join(path_to_files, str(user_id), relative_path[1:])
    new_abs_path = os.path.join(path_to_files, str(user_id), new_path[1:])
    if os.path.exists(abs_path) and not os.path.exists(new_abs_path):
        FTPDatabaseOperations.change_file_path_on_db(server_db, abs_path, new_abs_path)
        os.rename(abs_path, new_abs_path)
        compilation_queue.put_nowait('213 File name changed.')
    else:
        raise FTPExceptions.FileDoesNotExists


def share_file(params, user_id, path_to_files, server_db, command_queue, compilation_queue):
    """
    This command is not a valid ftp command. It will tell the server to share a specific file with
    other user, specified by user_name param. permissions arg is optional and it will indicate the
    permissions the shared user will have on this file. default permissions is  ()
    SHAR syntax: SHAR path_to_file user_name permissions(optional) SESSION=sessionid
    Example: RNTO \a\text.txt user123
    """
    relative_path, user_name = params
    abs_path = os.path.join(path_to_files, str(user_id), relative_path[1:])
    if os.path.exists(abs_path):
        if FTPDatabaseOperations.add_user_to_file_db(server_db, abs_path, user_name):
            compilation_queue.put_nowait('213 File shared successfully.')
        else:
            raise FTPExceptions.InternalError
    else:
        raise FTPExceptions.FileDoesNotExists


def mkdir(params, user_id, path_to_files, server_db, command_queue, compilation_queue):
    """
    Create a directory in the server.
    MKD stntax: MKD dir_path SESSION=sessionid
    """
    relative_path = params[0]
    abs_path = os.path.join(path_to_files, str(user_id), relative_path[1:])
    if os.path.exists(abs_path):
        raise FTPExceptions.FileAlreadyExists
    else:
        os.mkdir(abs_path)
        compilation_queue.put_nowait('212 Directory created.')


def rmdir(params, user_id, path_to_files, server_db, command_queue, compilation_queue):
    """
    Remove a directory on server
    RMD stntax: RMD dir_path SESSION=sessionid
    """
    relative_path = params[0]
    abs_path = os.path.join(path_to_files, str(user_id), relative_path[1:])
    if os.path.exists(abs_path):
        for directory in os.walk(abs_path, topdown=False):  # Iterate directory recursively
            for file_path in directory[2]:
                abs_file_path = os.path.join(directory[0], file_path)
                FTPDatabaseOperations.remove_file_from_db(server_db, abs_file_path, user_id)

        rmtree(abs_path)  # delete directory recursively
        compilation_queue.put_nowait('212 Directory deleted.')
    else:
        raise FTPExceptions.FileDoesNotExists

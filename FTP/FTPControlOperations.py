import os
from shutil import rmtree

import FTPExceptions
import FTPDatabaseOperations
import GroupOperations
from PermissionsConsts import *


def get_file_from_group_and_check_permission(group, relative_path, server_db, user_id,
                                             permission_filter, path_to_files):
    """
    This function will look for user's file in a specific group and will return the file specified by
    relative path only if the user has the permission specified with permission_filter. If group is empty
    string, the funtion will return absolute path to the file specified.
    If the user does not have the permission specified with permission_filter, the function will throw
    FTPExceptions.PermissionDenied exception. If permission_filter is 0, the function will not check for
    permission.
    """
    abs_path = ''
    if group == 'SHARED':
        files_with_permsission = FTPDatabaseOperations.get_all_files_associated_with_user(server_db,
                                 user_id, permission_filter=permission_filter)
        for shared_file in files_with_permsission:
            if relative_path in shared_file:
                abs_path = shared_file
        if not abs_path:
            raise FTPExceptions.PermissionDenied

    elif group == '':
        # File does not associated with a group
        abs_path = os.path.join(path_to_files, str(user_id), relative_path[1:])

    else:
        group_id = FTPDatabaseOperations.get_group_id_if_user_in_group(server_db, group, user_id)
        if group_id:
            abs_path = os.path.join(path_to_files, 'g' + str(group_id), relative_path[1:])
        else:
            raise FTPExceptions.NoSuchGroup

    return abs_path


def append_file(params, user_id, path_to_files, server_db, command_queue, completion_queue):
    """
    Add a file to the FTP server.
    command syntax: APPE file_path_on_server SESSIONID=sessionid
    """
    if len(params) == 2:
        relative_path, group = params
    else:
        relative_path, group = params[0], ''

    abs_path = get_file_from_group_and_check_permission(group, relative_path, server_db,
                                                        user_id, 0, path_to_files)
    print 'control: ', abs_path
    if group:
        command_queue.put_nowait(' '.join(['APPE', abs_path, group, 'USERID=' + str(user_id)]))
    else:
        command_queue.put_nowait(' '.join(['APPE', abs_path, 'USERID=' + str(user_id)]))


def get_file(params, user_id, path_to_files, server_db, command_queue, completion_queue):
    """
    Get a file from FTP server. if group is specified with GET, GET will get
    a file associated to a the specied group.
    command syntax: GET file_path_on_server group(optional) SESSIONID=sessionid
    """
    if len(params) == 2:
        relative_path, group = params
    else:
        relative_path, group = params[0], ''

    abs_path = get_file_from_group_and_check_permission(group, relative_path, server_db,
                                                        user_id, DOWNLOAD, path_to_files)
    if group:
        command_queue.put_nowait(' '.join(['GET', abs_path, group, 'USERID=' + str(user_id)]))
    else:
        command_queue.put_nowait(' '.join(['GET', abs_path, 'USERID=' + str(user_id)]))



def list_files(params, user_id, path_to_files, server_db, command_queue, completion_queue):
    """
    LIST command will list every file in dir_path. group is optional parameter and it indicates
    that the server should list files shared by this group. group parameter can be specified
    to "SHARED", this will tell the server to include files associated with the user, that
    he is not their owner (the files shared with the user)
    LIST stntax: LIST dir_path group(optional) SESSIONID=sessionid
    """
    command_queue.put_nowait(' '.join(['LIST'] + params + ['USERID=' + str(user_id)]))


def delete_file(params, user_id, path_to_files, server_db, command_queue, completion_queue):
    """
    Delete a file on server.
    DELE stntax: DELE file_name group(optional) SESSIONID=sessionid
    """
    if len(params) == 2:
        relative_path, group = params
    else:
        relative_path, group = params[0], ''

    abs_path = get_file_from_group_and_check_permission(group, relative_path, server_db,
                                                        user_id, DELETE, path_to_files)

    if os.path.exists(abs_path):
        FTPDatabaseOperations.remove_file_from_db(server_db, abs_path, user_id)
        os.remove(abs_path)
        completion_queue.put_nowait('213 File deleted.')
    else:
        raise FTPExceptions.FileDoesNotExists


def rename_file(params, user_id, path_to_files, server_db, command_queue, completion_queue):
    """
    On standart ftp servers, to rename a file the client must enter RNFR command
    and RNTO command right after it. On this implementation, the client need to
    enter only RNTO command with 2 parameters.
    RNTO syntax: RNTO path_to_file path_to_new_file group(optional) SESSIONID=sessionid
    Example: RNTO \a\b\before.txt \a\b\after.txt
    """
    if len(params) == 3:
        relative_path, new_path, group = params
    else:
        relative_path, new_path = params
        group = ''

    abs_path = get_file_from_group_and_check_permission(group, relative_path, server_db,
                                                        user_id, RENAME, path_to_files)

    new_abs_path = os.path.join(path_to_files, str(user_id), new_path[1:])
    if os.path.exists(abs_path):
        if not os.path.exists(new_abs_path):
            FTPDatabaseOperations.change_file_path_on_db(server_db, abs_path, new_abs_path)
            os.rename(abs_path, new_abs_path)
            completion_queue.put_nowait('213 File name changed.')
        else:
            raise FTPExceptions.FileAlreadyExists
    else:
        raise FTPExceptions.FileDoesNotExists

def mkdir(params, user_id, path_to_files, server_db, command_queue, completion_queue):
    """
    Create a directory in the server.
    MKD stntax: MKD dir_path group(optional) SESSIONID=sessionid
    """
    if len(params) == 2:
        relative_path, group = params
        group_id = FTPDatabaseOperations.get_group_id_if_user_in_group(server_db, group, user_id)
        abs_path = os.path.join(path_to_files, 'g' + str(group_id), relative_path[1:])
    else:
        relative_path, group = params[0], ''
        abs_path = os.path.join(path_to_files, str(user_id), relative_path[1:])

    if os.path.exists(abs_path):
        raise FTPExceptions.FileAlreadyExists
    else:
        os.mkdir(abs_path)
        completion_queue.put_nowait('212 Directory created.')


def rmdir(params, user_id, path_to_files, server_db, command_queue, completion_queue):
    """
    Remove a directory on server
    RMD stntax: RMD dir_path group(optional) SESSIONID=sessionid
    """
    if len(params) == 2:
        relative_path, group = params
        group_id = FTPDatabaseOperations.get_group_id_if_user_in_group(server_db, group, user_id)
        abs_path = os.path.join(path_to_files, 'g' + str(group_id), relative_path[1:])
    else:
        relative_path, group = params[0], ''
        abs_path = os.path.join(path_to_files, str(user_id), relative_path[1:])

    if os.path.exists(abs_path):
        for directory in os.walk(abs_path, topdown=False):  # Iterate directory recursively
            for file_path in directory[2]:
                abs_file_path = os.path.join(directory[0], file_path)
                FTPDatabaseOperations.remove_file_from_db(server_db, abs_file_path, user_id)

        rmtree(abs_path)  # delete directory recursively
        completion_queue.put_nowait('212 Directory deleted.')
    else:
        print abs_path
        raise FTPExceptions.FileDoesNotExists


def share_file(params, user_id, path_to_files, server_db, command_queue, completion_queue):
    """
    This command is not a valid ftp command. It will tell the server to share a specific file with
    other user, specified by user_name param. permissions argument will indicate the
    permissions the shared user will have on this file. permissions is a number formatted with flags
    according to the flags written on permission_doc.txt file.
    SHAR syntax: SHAR path_to_file user_name permissions group(optional) SESSIONID=sessionid
    """
    if len(params) == 4:
        relative_path, user_name, permissions, group = params
    else:
        relative_path, user_name, permissions = params
        group = ''

    abs_path = get_file_from_group_and_check_permission(group, relative_path, server_db,
                                                        user_id, SHARE, path_to_files)

    if os.path.exists(abs_path):
        if FTPDatabaseOperations.add_user_to_file_db(server_db, abs_path, user_name, permissions=permissions):
            completion_queue.put_nowait('213 File shared successfully.')
        else:
            raise FTPExceptions.InternalError
    else:
        raise FTPExceptions.FileDoesNotExists

def group_operations(params, user_id, path_to_files, server_db, command_queue, completion_queue):
    """
    This command is not a valid ftp command.
    The command has several uses:

    GROUP GET:
    The command will tell the server to return all the groups that the user
    is in them. The server will reply with "211 group_name1,group_name2,group_name3..."
    GROUP GET syntax: GROUP GET SESSIONID=sessionid

    GROUP JOIN:
    The command will tell the server to connect the user to a group.
    GROUP JOIN syntax: GROUP JOIN group_name group_password SESSIONID=sessionid

    GROUP CREATE:
    The command will tell the server to create a new group, and connect the user to this group with
    OWNER permissions.
    GROUP JOIN syntax: GROUP CREATE group_name group_password SESSIONID=sessionid

    GROUP LIST:
    The command will tell the server to return all the users of a given group. The server
    will reply with "211 username1,username2,username3...". The first username is always the username of
    the owner of this group.
    GROUP LIST syntax: GROUP LIST group_name SESSIONID=sessionid

    GROUP DELETE:
    The command will tell the server to delete the given group.
    GROUP DELETE syntax: GROUP DELETE group_name SESSIONID=sessionid

    GROUP REMOVE:
    The command will tell the server to remove the given user from the given group.
    GROUP REMOVE syntax: GROUP REMOVE group_name username SESSIONID=sessionid
    """

    operations = {'GET':GroupOperations.group_get,
                  'CREATE':GroupOperations.group_create,
                  'JOIN':GroupOperations.group_join,
                  'LIST': GroupOperations.group_list,
                  'DELETE': GroupOperations.group_delete,
                  'REMOVE': GroupOperations.group_remove }

    if len(params) >= 3:
        completion_queue.put_nowait(operations[params[0]](params[1], params[2], server_db, user_id))
    elif len(params) == 2:
        completion_queue.put_nowait(operations[params[0]](params[1], server_db, user_id))
    else:
        completion_queue.put_nowait(operations[params[0]](server_db, user_id))

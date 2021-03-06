import os
from shutil import rmtree

import FTPDatabaseOperations
import FTPExceptions


def group_get(server_db, user_id):
    return '211 ' + ','.join(FTPDatabaseOperations.get_user_groups(server_db, user_id))

def group_join(group_name, group_password, server_db, user_id):
    error_code = FTPDatabaseOperations.join_group(server_db, group_name, group_password, user_id)
    if error_code == 0:
        return '211 Group joined successfully'
    elif error_code == 1:
        raise FTPExceptions.NoSuchGroup
    else:
        raise FTPExceptions.InvalidGroupPassword

def group_create(group_name, group_password, server_db, user_id):
    if FTPDatabaseOperations.create_group(server_db, group_name, group_password, user_id):
        return '211 Group created successfully'
    else:
        raise FTPExceptions.GroupAlreadyExists

def group_list(group_name, server_db, user_id):
    return '211 ' + ','.join(FTPDatabaseOperations.get_users_in_group(server_db, group_name))

def group_remove(group_name, username_to_remove, server_db, user_id):
    if FTPDatabaseOperations.remove_user_from_group(server_db, group_name, username_to_remove):
        return '211 User removed from group successfully'
    else:
        raise FTPExceptions.NoSuchGroup

def group_delete(group_name, server_db, user_id, path_to_files):
    group_id = FTPDatabaseOperations.get_group_id_if_user_in_group(server_db, group_name, user_id)
    dir_path = os.path.join(path_to_files, 'g' + str(group_id))
    if os.path.exists(dir_path):
        if os.path.isdir(dir_path):
            rmtree(dir_path)
    if FTPDatabaseOperations.delete_group(server_db, group_name):
        return '211 Group deleted successfully'
    else:
        raise FTPExceptions.NoSuchGroup

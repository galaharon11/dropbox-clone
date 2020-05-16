import FTPDatabaseOperations
import FTPExceptions

def group_get(user_id, server_db, complition_queue):
    return '211 ' + ','.join(FTPDatabaseOperations.get_user_groups(server_db, user_id))

def group_join(group_name, group_password, server_db, user_id, complition_queue):
    error_code = FTPDatabaseOperations.join_group(server_db, group_name, group_password, user_id)
    if error_code == 0:
        return '211 Group created successfully'
    elif error_code == 1:
        raise FTPExceptions.NoSuchGroup
    else:
        raise FTPExceptions.InvalidGroupPassword

def group_create(group_name, group_password, server_db, user_id, complition_queue):
    if FTPDatabaseOperations.create_group(server_db, group_name, group_password, user_id):
        return '211 Group created successfully'
    else:
        raise FTPExceptions.GroupAlreadyExists

import FTPDatabaseOperations
import FTPExceptions

def group_get(user_id, server_db, complition_queue):
    return '211 ' + ','.join(FTPDatabaseOperations.get_user_groups(server_db, user_id))

def group_join(group_name, server_db, user_id, complition_queue):
    if FTPDatabaseOperations.join_group(server_db, group_name, user_id):
        return '211 Group created successfully'
    else:
        raise FTPExceptions.NoSuchGroup

def group_create(group_name, server_db, user_id, complition_queue):
    if FTPDatabaseOperations.create_group(server_db, group_name, user_id):
        return '211 Group created successfully'
    else:
        raise FTPExceptions.GroupAlreadyExists

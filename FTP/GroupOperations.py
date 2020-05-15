import FTPDatabaseOperations

def group_get(server_db, user_id, complition_queue):
    complition_queue.put_nowait('211 '+ ','.join(FTPDatabaseOperations.get_user_groups(server_db)))

def group_join(group_name, server_db, user_id, complition_queue):
    FTPDatabaseOperations.join_group(server_db, group_name, user_id)


def group_create(group_name, server_db, user_id, complition_queue):
    if FTPDatabaseOperations.create_group(server_db, group_name, user_id):
        complition_queue.put_nowait('211 Group created successfully')
    else:
        complition_queue.put_nowait('550 Group already exists')

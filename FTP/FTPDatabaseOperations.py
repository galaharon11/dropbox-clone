from PermissionsConsts import *

def add_user_to_file_db(server_db, file_path, user_name, permissions=0):
    cursor = server_db.cursor()
    cursor.execute('''SELECT file_id FROM files WHERE file_path=?''', (file_path,))
    file_id = cursor.fetchone()
    if not file_id:
        return False
    file_id = int(file_id[0])
    cursor.execute('''SELECT user_id FROM users WHERE username=?''', (user_name,))
    user_id = cursor.fetchone()
    if not user_id:
        return False
    user_id = int(user_id[0])
    cursor.execute('''INSERT INTO users_files VALUES (?, ?, ?)''', (user_id, file_id, permissions))
    server_db.commit()
    return True

def add_file_to_db(server_db, file_path, user_id, is_dir=False, permissions=OWNER):
    cursor = server_db.cursor()
    cursor.execute('''INSERT INTO files VALUES (null, ?, ?)''', (file_path, is_dir))
    server_db.commit()
    cursor.execute('''SELECT file_id FROM files WHERE file_path=?''', (file_path,))
    file_id = int(cursor.fetchone()[0])
    cursor.execute('''INSERT INTO users_files VALUES (? , ?, ?)''', (user_id, file_id, permissions))
    server_db.commit()

def remove_file_from_db(server_db, file_path, user_id, is_dir=False, permissions=OWNER):
    cursor = server_db.cursor()
    cursor.execute('''SELECT file_id FROM files WHERE file_path=?''', (file_path,))
    file_id = int(cursor.fetchone()[0])
    cursor.execute('''DELETE FROM users_files WHERE file_id=?''', (file_id,))
    cursor.execute('''DELETE FROM files WHERE file_id=?''', (file_id,))
    server_db.commit()

def get_all_files_associated_with_user(server_db, user_id, permission_filter=0, reverse_filter=False):
    '''
    Get all files associated with user specified by user_id. if permission_filter is non-zero,
    the function will filter files with the permission specified or the OWNER permission. If reverse_filter
    is True, the function will return every file that associated with the user that does not contain
    permission_filter or OWNER for the user specified.
    '''
    permission_filter |= OWNER
    cursor = server_db.cursor()
    cursor.execute('''SELECT file_id, permissions FROM users_files WHERE user_id=?''', (user_id,))
    queries = set(cursor.fetchall())
    print queries
    if permission_filter:
        filtered = set(filter(lambda query: (query[1] & permission_filter) != 0, queries))
        print filtered, permission_filter
        queries = queries - filtered if reverse_filter else filtered

    file_ids = [str(q[0]) for q in queries]
    cursor.execute('''SELECT file_path FROM files WHERE file_id IN ({0})'''.format(','.join(file_ids)))
    a = cursor.fetchall()
    return [query[0] for query in a]

def check_permissions(server_db, file_path, user_id, permission=OWNER):
    """
    Check if a given user, specified with user_id, have the specied permission specified in permissions arg
    on the given file specified with file_path. This function will return True if the user has
    the permission specified or if he has the OWNER permission
    """
    permission = permission | OWNER
    cursor = server_db.cursor()
    cursor.execute('''SELECT file_id FROM files WHERE file_path=?''', (file_path,))
    file_id = int(cursor.fetchone()[0])
    cursor.execute('''SELECT user_id, permissions FROM users_files WHERE file_id=?''', (file_id,))
    user_id_from_db, permissions_from_db = cursor.fetchone()
    if int(user_id_from_db) == user_id:
        if (int(permissions_from_db) & permission) != 0:
            return True
    return False


def change_file_path_on_db(server_db, file_path, new_file_path, permissions=1):
    cursor = server_db.cursor()
    cursor.execute('''UPDATE files SET file_path=? WHERE file_path=?''', (new_file_path, file_path))
    server_db.commit()

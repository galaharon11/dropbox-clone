from sqlite3 import IntegrityError

from PermissionsConsts import *
import FTPExceptions


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

def add_file_to_db(server_db, file_path, user_id, is_dir=False, group='', permissions=OWNER):
    cursor = server_db.cursor()
    if group:
        print 'group', group
        group_id = get_group_id_if_user_in_group(server_db, group, int(user_id))
        print 'id', group_id
        if group_id:
            cursor.execute('''INSERT INTO files VALUES (null, ?, ?, ?)''', (file_path, is_dir, group_id))
        else:
            raise FTPExceptions.PermissionDenied
    else:
        cursor.execute('''INSERT INTO files VALUES (null, ?, ?, null)''', (file_path, is_dir))

    server_db.commit()
    cursor.execute('''SELECT file_id FROM files WHERE file_path=?''', (file_path,))
    file_id = int(cursor.fetchone()[0])
    cursor.execute('''INSERT INTO users_files VALUES (?, ?, ?)''', (user_id, file_id, permissions))
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
    return [query[0] for query in cursor.fetchall()]

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

def create_group(server_db, group_name, group_password, user_id):
    try:
        cursor = server_db.cursor()
        cursor.execute('''INSERT INTO groups VALUES (null, ?, ?)''', (group_name, group_password))
        server_db.commit()
        cursor.execute('''SELECT group_id FROM groups WHERE group_name=?''', (group_name,))
        group_id = int(cursor.fetchone()[0])

        cursor.execute('''INSERT INTO users_groups VALUES (?, ?, ?)''', (user_id, group_id, OWNER))
        server_db.commit()
    except IntegrityError as e:
        print str(e)
        return False
    return True

def get_user_groups(server_db, user_id):
    cursor = server_db.cursor()
    cursor.execute('''SELECT group_id FROM users_groups WHERE user_id=?''', (user_id,))
    group_ids = cursor.fetchall()
    group_ids = map(lambda x: str(x[0]), group_ids)
    print ','.join(group_ids)
    cursor.execute('''SELECT group_name FROM groups WHERE group_id IN ({0})'''.format(','.join(group_ids)))
    group_names = cursor.fetchall()
    if group_names:
        group_names = map(lambda x: x[0], group_names)
        return list(group_names)
    else:
        return []

def join_group(server_db, group_name, group_password, user_id, permissions=1):
    """
    The function will return 0 if sucess, 1 if the group does not exists and 2 if
    the password is incorrect.
    """
    cursor = server_db.cursor()

    cursor.execute('''SELECT group_id, group_password FROM groups WHERE group_name=?''', (group_name,))
    query = cursor.fetchone()
    if not query:
        return 1

    if group_password != query[1]:
        return 2

    group_id = int(query[0])
    cursor.execute('''INSERT INTO users_groups VALUES (?, ?, ?)''', (user_id, group_id, permissions))
    server_db.commit()
    return 0

def get_group_id_if_user_in_group(server_db, group_name, user_id):
    cursor = server_db.cursor()
    cursor.execute('''SELECT group_id FROM groups WHERE group_name=?''', (group_name,))
    group_id = cursor.fetchone()
    if not group_id:
        print group_name, 'group_name invalid'
        return False
    group_id = int(group_id[0])
    cursor.execute('''SELECT user_id FROM users_groups WHERE group_id=?''', (group_id,))
    users_in_group = map(lambda x: x[0], cursor.fetchall())
    if user_id in users_in_group:
        return group_id
    else:
        print group_name, 'user not in this group'
        return False

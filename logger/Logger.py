import time
from datetime import datetime

from FTP.FTPDatabaseOperations import get_username_for_id


class Log(object):
    """
    Log will hold info about operations on the server. There are 4 types of operations:
    'file' - A user has downloaded a file or uploaded one.
    'group' - A user has created a group or deleted a group.
    'error' - A user tried to do an illegal operation. For example, a user without delete permission
              on a file tries to delete the file.
    'user' - A user was registered or logged in.
    """
    def _format(self):
        description = unicode(self.message)
        format_list = []
        if self.username:
            format_list.append(self.username)
        if self.file_path:
            format_list.append(self.file_path)
        if self.group_name:
            format_list.append(self.group_name)
        return description.format(*format_list)

    def __init__(self, operation_type, message, server_db, file_path='', username=0, group_name=''):
        self.operation_type = operation_type
        self.message = message

        self.file_path = file_path
        self.username = username
        self.group_name = group_name

        cursor = server_db.cursor()
        cursor.execute('''INSERT INTO logger VALUES (?, ?, strftime('%s','now'))''', (operation_type,
                                                                                      self._format()))
        server_db.commit()


class Logger(object):
    def __init__(self, server_db):
        self.server_db = server_db

    def add_file_log(self, message, user_id, file_path):
        """
        Add a log of type 'file'.
        """
        username = get_username_for_id(self.server_db, user_id)
        Log('file', message, self.server_db, username=username, file_path=file_path)

    def add_error_log(self, error, user_id=0):
        """
        Add a log of type 'error'.
        error parameter should be an error message or FTPException.
        """
        if user_id:
            username = get_username_for_id(self.server_db, user_id)
            Log('error', str(error), self.server_db, username=username)
        else:
            self.log.append(Log('error', str(error)))

    def add_group_log(self, message, group_name):
        """
        Add a log of type 'group'.
        """
        Log('group', message, self.server_db, group_name=group_name)

    def add_user_log(self, message, user_id):
        """
        Add a log of type 'user'.
        """
        username = get_username_for_id(self.server_db, user_id)
        Log('user', message, self.server_db, username=username)

    def get_logs(self, n=30, operation_type='user'):
        """
        Get the 'n' latest logs (default 30 logs) of type 'operation_type'. 'operation_type' can be
        one of the strings 'file', 'user', 'group', 'error'. Returns a list of touples: [(log_message1, log_time1),
        (log_message2, log_time2)...]
        """
        cursor = self.server_db.cursor()
        cursor.execute('''SELECT message, datetime(timestemp, 'unixepoch') FROM logger WHERE type=?
                          ORDER BY timestemp ASC LIMIT ?''', (operation_type, str(n)))

        return cursor.fetchall()

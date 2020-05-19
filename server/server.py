import socket
import sqlite3 as sqlite
import threading
import sys, os

from FTP.FTPServer import FTPServer
from logger.Logger import Logger
from admin.AdminWindow import AdminWindow


server_ip = '127.0.0.1'
PORT = 10054
sessions_id_list = {}
db = None
logger = None

def handle_admin(path_to_files):
    try:
        while True:
            print 'Enter \'admin\' to access admin mode or \'quit\' to stop the server.'
            command = raw_input('> ')
            if command == 'admin':
                AdminWindow(db, logger, path_to_files)
            elif command == 'quit':
                os._exit(0)
            else:
                print 'Unknown command.'

    except EOFError, IOError:
        # Admin ctrl-z
        pass


def handle_connection(sock, addr, ftp_server, logger):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                sock.close()
                return
            if data.startswith("login;"):
                data = data.split(';')
                if len(data) != 3:
                    raise ValueError
                username = data[1]
                password = data[2]
                register = False

            elif data.startswith("register;"):
                data = data.split(';')
                if len(data) != 4:
                    raise ValueError
                name = data[1]
                username = data[2]
                password = data[3]
                register_user(name, username, password)
                register = True

            elif data == 'quit':
                sock.close()
                return
            else:
                raise ValueError

            user = login_user(username, password)
            if not user:
                raise AttributeError

            if register:
                logger.add_user_log('User {0} register.', user[0])
            else:
                logger.add_user_log('User {0} login.', user[0])

            sock.send('success')

            session_id = ftp_server.add_session_id(user[0])
            sock.send('SESSIONID {0}'.format(str(session_id)))
            sock.close()
            return

        except sqlite.IntegrityError:
            sock.send('Username already taken')
        except AttributeError as e:
            sock.send('Username or password are incorrect')
        except ValueError, sqlite.Error:
            print 'Unexpected error'
            logger.add_error_log('Unexpected error.')
            sock.send('Unexpected error')
        except socket.error as e:
            # Client closed program with ctrl+c
            if e.errno == 10054:
                return


def login_user(username, password):
    cursor = db.cursor()
    cursor.execute('''SELECT * FROM users WHERE username=? and password=?''', (username, password))
    user = cursor.fetchone()
    return user


def register_user(name, username, password):
    cursor = db.cursor()
    cursor.execute('''INSERT INTO users VALUES (null, ?, ?, ?)''', (name, username, password))
    db.commit()


def create_db():
    global db
    try:
        # check if file exists and connect
        db_file = open('server.db', 'r')
        db_file.close()
        db = sqlite.connect('server.db', check_same_thread=False)
    except IOError:
        print "Database does not found, creating it..."
        # file does not exist
        db_file = open('server.db', 'w')
        db_file.close()
        db = sqlite.connect('server.db', check_same_thread=False)
        cursor = db.cursor()
        # enable foreign_keys contrain with sqlite
        cursor.execute('''PRAGMA foreign_keys = ON;''')

        cursor.execute('''CREATE TABLE users (
                        user_id INTEGER PRIMARY KEY NOT NULL,
                        name TEXT NOT NULL,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')

        cursor.execute('''CREATE TABLE groups (
                        group_id INTEGER PRIMARY KEY NOT NULL,
                        group_name TEXT UNIQUE NOT NULL,
                        group_password TEXT NOT NULL )''')

        # One to many relationship between files and groups.A file may be assoicated with user.
        # and not with group, if that is the case group_id will be null.
        cursor.execute('''CREATE TABLE files (
                        file_id INTEGER PRIMARY KEY NOT NULL,
                        file_path TEXT UNIQUE NOT NULL,
                        is_directory INT1,
                        group_id INTETGER,
                        FOREIGN KEY(group_id) REFERENCES groups (group_id) )''')


        # Many to many relationship between users and files
        cursor.execute('''CREATE TABLE users_files (
                        user_id INTEGER NOT NULL,
                        file_id INTEGER NOT NULL,
                        permissions INT1,
                        FOREIGN KEY(user_id) REFERENCES users (user_id),
                        FOREIGN KEY(file_id) REFERENCES files (file_id) )''')

        # Many to many relationship between users and groups
        cursor.execute('''CREATE TABLE users_groups (
                        user_id INTEGER NOT NULL,
                        group_id INTEGER NOT NULL,
                        permissions INT1,
                        FOREIGN KEY(user_id) REFERENCES users (user_id),
                        FOREIGN KEY(group_id) REFERENCES groups (group_id) )''')

        cursor.execute('''CREATE TABLE logger (
                        type TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestemp INTEGER NOT NULL )''')

        db.commit()
        print "Database created."


def main():
    global login_socket, logger

    create_db()
    logger = Logger(db)

    ftp_server = FTPServer(server_ip, db, logger)

    login_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    login_socket.bind((server_ip, PORT))
    login_socket.listen(5)
    # Without settimeout server wont be able to quit using ctrl-z
    login_socket.settimeout(0.1)

    print 'Server is up and running!'
    admin_thread = threading.Thread(target=handle_admin, args=(ftp_server.path_to_files,))
    admin_thread.daemon = True  # Exit thread when program ends
    admin_thread.start()

    while True:
        try:
            clientsock, client_addr = login_socket.accept()
            thread = threading.Thread(target=handle_connection, args=(clientsock, client_addr, ftp_server, logger))
            thread.daemon = True  # Exit thread when program ends
            thread.start()
        except socket.timeout:
            pass


if __name__ == '__main__':
    try:
        # This line allows modules to import python files within the program
        sys.path.append(os.path.dirname(sys.path[0]))
        main()
    except KeyboardInterrupt, SystemExit:
        db.close()
        login_socket.close()
        exit()

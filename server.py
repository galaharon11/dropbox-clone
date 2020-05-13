import socket
import sqlite3 as sqlite
import threading
import traceback

from FTPServer import FTPServer

server_ip = "10.100.102.15"
PORT = 10054
sessions_id_list = {}
db = None


def handle_connection(sock, addr, ftp_server):
    while True:
        try:
            data = sock.recv(1024)
            print data
            if not data:
                sock.close()
                return
            if data.startswith("login;"):
                # TODO: User cant use ; on username
                data = data.split(';')
                if len(data) != 3:
                    raise ValueError
                username = data[1]
                password = data[2]

            elif data.startswith("register;"):
                # TODO: User cant use ; on username
                data = data.split(';')
                if len(data) != 4:
                    raise ValueError
                name = data[1]
                username = data[2]
                password = data[3]
                register_user(name, username, password)

            elif data == 'quit':
                sock.close()
                return
            else:
                print data
                raise ValueError

            user = login_user(username, password)
            if not user:
                raise AttributeError

            print 'User login', user
            sock.send('success')

            session_id = ftp_server.add_session_id(user[0])
            sock.send('SESSIONID {0}'.format(str(session_id)))
            sock.close()
            return

        except sqlite.IntegrityError:
            sock.send('Username already taken')
        except AttributeError:
            sock.send('Username or password are incorrect')

        except (ValueError, sqlite.Error):
            traceback.print_exc()
            print ('Unexpected error')
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
        # file does not exist
        db_file = open('server.db', 'w')
        db_file.close()
        print "created file"
        db = sqlite.connect('server.db', check_same_thread=False)
        cursor = db.cursor()
        # enable foreign_keys contrain with sqlite
        cursor.execute('''PRAGMA foreign_keys = ON;''')

        cursor.execute('''CREATE TABLE users (
                        user_id INTEGER PRIMARY KEY NOT NULL,
                        name TEXT NOT NULL,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE files (
                        file_id INTEGER PRIMARY KEY NOT NULL,
                        file_path TEXT UNIQUE NOT NULL,
                        is_directory INT1 )''')
        # Many to many relationship
        cursor.execute('''CREATE TABLE users_files (
                        user_id INTEGER NOT NULL,
                        file_id INTEGER NOT NULL,
                        permissions INT1,
                        FOREIGN KEY(user_id) REFERENCES users (user_id),
                        FOREIGN KEY(file_id) REFERENCES files (file_id) )''')

        db.commit()


def main():
    global login_socket

    create_db()
    ftp_server = FTPServer(server_ip, db)

    login_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    login_socket.bind((server_ip, PORT))
    login_socket.listen(5)
    # Without settimeout server wont be able to quit using ctrl-z
    login_socket.settimeout(0.1)

    while True:
        try:
            clientsock, client_addr = login_socket.accept()
            thread = threading.Thread(target=handle_connection, args=(clientsock, client_addr, ftp_server))
            thread.daemon = True  # Exit thread when program ends
            thread.start()
        except socket.timeout:
            pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt, SystemExit:
        db.close()
        login_socket.close()
        exit()

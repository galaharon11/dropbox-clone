
import tkMessageBox
import socket
import select

from passive_connect import passive_connect


def list_directory_by_path(server_path, session_id, control_sock, server_ip, group=''):
    """
    Asks the server to list files in the directory specifies in path parameter.
    The server should response with the name of the each file inside this directory, seperated
    by semicolon. When the server finish sending the file names, it will send a triple semicolon,
    and then it will send each subdirectory name inside of the directory the program asked for.

    param path: path to the new directory.

    returns: a touple of two lists: first one is file names list and the second is directory names list.
    """

    data_sock = passive_connect(control_sock, server_ip)
    data_sock.settimeout(0.1)

    if group:
        control_sock.send('|'.join(['LIST', server_path, group, 'SESSIONID=' + str(session_id)]).encode('utf8'))
    else:
        control_sock.send('|'.join(['LIST', server_path, 'SESSIONID=' + str(session_id)]).encode('utf8'))

    attemps_counter = 0
    try:
        data = data_sock.recv(1024)
    except socket.timeout:
        attemps_counter += 1
        read_sockets, write_sockets, error_sockets = select.select([control_sock], [], [])
        if control_sock in read_sockets:
            error = control_sock.recv(1024)
            err_msg = error
            if error.startswith('550'):
                if group:
                    return

        if attemps_counter == 100:
            raise IOError


    files, dirs = data.decode('utf8').split(';;;')
    files = filter(lambda name: name, files.split(','))
    dirs = filter(lambda name: name, dirs.split(','))
    data_sock.close()
    print control_sock.recv(1024)
    return((files, dirs))


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
    if group:
        control_sock.send(' '.join(['LIST', server_path, group, 'SESSIONID=' + str(session_id)]).encode('utf8'))
    else:
        control_sock.send(' '.join(['LIST', server_path, 'SESSIONID=' + str(session_id)]).encode('utf8'))
    files, dirs = data_sock.recv(1024).decode('utf8').split(';;;')
    files = filter(lambda name: name, files.split(','))
    dirs = filter(lambda name: name, dirs.split(','))
    data_sock.close()
    print control_sock.recv(1024)
    return((files, dirs))

from os import path
import tkMessageBox
import socket
import select
from sys import stdin

from passive_connect import passive_connect


def upload_file_by_path(file_path, server_path, control_sock, session_id, server_ip):
    if not path.exists(file_path):
        raise IOError

    attemps_counter = 0
    data_sock = passive_connect(control_sock, server_ip)
    data_sock.settimeout(0.1)
    control_sock.send(' '.join(['APPE', path.join(server_path, path.basename(file_path)),
                                'SESSIONID=' + str(session_id)]))
    try:
        file_to_upload = open(file_path, 'rb')
        data_sock.send(file_to_upload.read())
    except IOError:
        tkMessageBox.showerror(title='Error', message='The directory you chose already contains a'
                                                      'file with the same name, please choose antoher directory')
    except socket.timeout:
        attemps_counter += 1
        read_sockets, write_sockets, error_sockets = select.select([stdin, control_sock], [], [])
        if control_sock in read_sockets:
            error = control_sock.read(1024)
            print error
            if error.startswith('5'):
                data_sock.close()
                file_to_upload.close()
                return error

        if attemps_counter == 100:
            raise IOError
    finally:
        data_sock.close()
        file_to_upload.close()
        return control_sock.recv(1024)

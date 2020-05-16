import os
import tkMessageBox
import socket
import select
from sys import stdin

from passive_connect import passive_connect

def _close_connection(data_sock, file_to_upload, queue, control_sock, err_msg):
    data_sock.close()
    file_to_upload.close()
    if err_msg:
        queue.put_nowait(err_msg)
    else:
        a = control_sock.recv(1024)
        queue.put_nowait(a)


def upload_file_by_path(file_path, server_path, control_sock, session_id, server_ip, progressbar, queue, group=''):
    if not os.path.exists(file_path):
        raise IOError

    attemps_counter = 0
    data_sock = passive_connect(control_sock, server_ip)
    data_sock.settimeout(0.1)
    if group:
        control_sock.send(' '.join(['APPE', os.path.join(server_path, os.path.basename(file_path)),
                                    group, 'SESSIONID=' + str(session_id)]).encode('utf8'))
    else:
        control_sock.send(' '.join(['APPE', os.path.join(server_path, os.path.basename(file_path)),
                                    'SESSIONID=' + str(session_id)]).encode('utf8'))

    err_msg = ''
    file_to_upload = open(file_path, 'rb')
    byte_counter = 0
    file_size = os.stat(file_path).st_size
    try:
        while byte_counter < file_size:
            file_to_upload.seek(byte_counter)
            data = file_to_upload.read(1024)
            byte_counter += len(data)
            data_sock.send(data)
            queue.put_nowait('bytes {0}'.format(byte_counter))

    except IOError:
        tkMessageBox.showerror(title='Error', message='The directory you chose already contains a'
                                                      'file with the same name, please choose antoher directory')
    except socket.timeout:
        attemps_counter += 1
        read_sockets, write_sockets, error_sockets = select.select([stdin, control_sock], [], [])
        if control_sock in read_sockets:
            error = control_sock.read(1024)
            err_msg = error
            if error.startswith('5'):
                _close_connection(data_sock, file_to_upload, queue, control_sock, err_msg)
                return

        if attemps_counter == 1000:
            raise IOError

    _close_connection(data_sock, file_to_upload, queue, control_sock, err_msg)

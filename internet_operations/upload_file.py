import os
import tkMessageBox
import socket
import select
from sys import stdin

from passive_connect import passive_connect


def upload_file_by_path(file_path, server_path, control_sock, session_id, server_ip, progressbar, queue):
    if not os.path.exists(file_path):
        raise IOError

    attemps_counter = 0
    data_sock = passive_connect(control_sock, server_ip)
    data_sock.settimeout(0.1)
    control_sock.send(' '.join(['APPE', os.path.join(server_path, os.path.basename(file_path)),
                                'SESSIONID=' + str(session_id)]))
    file_to_upload = open(file_path, 'rb')
    byte_counter = 0
    file_size = os.stat(file_path).st_size
    try:
        while byte_counter < file_size:
            file_to_upload.seek(byte_counter)
            data = file_to_upload.read(1024)
            byte_counter += len(data)
            data_sock.send(data)
            progressbar.set_byte_coutner(byte_counter)

    except IOError:
        tkMessageBox.showerror(title='Error', message='The directory you chose already contains a'
                                                      'file with the same name, please choose antoher directory')
    except socket.timeout:
        attemps_counter += 1
        read_sockets, write_sockets, error_sockets = select.select([stdin, control_sock], [], [])
        if control_sock in read_sockets:
            error = control_sock.read(1024)
            if error.startswith('5'):
                data_sock.close()
                file_to_upload.close()
                queue.put_nowait(error)

        if attemps_counter == 1000:
            raise IOError
    finally:
        data_sock.close()
        file_to_upload.close()
        queue.put_nowait(control_sock.recv(1024))

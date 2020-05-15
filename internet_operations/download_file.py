import socket
from sys import stdin
import select
import os

from passive_connect import passive_connect


def download_file_by_path(server_path, path_to_store_file, control_sock, session_id, server_ip, progressbar,
                          queue, group=''):
    """
    Downloads a file in the server by the given server_path. The downloaded file will be saved
    in path_to_store_file path, which sould be a valid path to a file in client's computer.
    If the file exists, it will be overriten, if it does not exists, it will be created.
    """
    file_to_download_to = open(path_to_store_file, 'wb')

    attemps_counter = 0
    data_sock = passive_connect(control_sock, server_ip)
    data_sock.settimeout(0.1)

    if group:
        control_sock.send(' '.join(['GET', server_path, group, 'SESSIONID=' + str(session_id)]))
    else:
        control_sock.send(' '.join(['GET', server_path, 'SESSIONID=' + str(session_id)]))

    byte_counter = 0
    file_size = int(data_sock.recv(1024))
    print file_size
    progressbar.update_file_size(file_size)
    while True:
        try:
            while byte_counter < file_size:
                data = data_sock.recv(1024)
                if not data:
                    break
                print byte_counter
                file_to_download_to.seek(byte_counter)
                file_to_download_to.write(data)
                byte_counter += len(data)
                queue.put_nowait('bytes {0}'.format(byte_counter))

        except socket.timeout:
            attemps_counter += 1
            read_sockets, write_sockets, error_sockets = select.select([stdin, control_sock], [], [])
            if control_sock in read_sockets:
                error = control_sock.recv(1024)
                if error.startswith('5'):
                    data_sock.close()
                    file_to_download_to.close()
                    queue.put_nowait(error)
                    return

            if attemps_counter == 100:
                raise IOError
        finally:
            data_sock.close()
            file_to_download_to.close()
            queue.put_nowait(control_sock.recv(1024))
            return

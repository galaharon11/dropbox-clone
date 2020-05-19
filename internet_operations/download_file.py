import socket
import select
import os

from passive_connect import passive_connect


def _close_connection(data_sock, file_to_download_to, queue, control_sock, err_msg):
    data_sock.close()
    file_to_download_to.close()
    if err_msg:
        queue.put_nowait(err_msg)
    else:
        queue.put_nowait(control_sock.recv(1024))


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
        control_sock.send('|'.join(['GET', server_path, group, 'SESSIONID=' + str(session_id)]).encode('utf8'))
    else:
        control_sock.send('|'.join(['GET', server_path, 'SESSIONID=' + str(session_id)]).encode('utf8'))

    byte_counter = 0
    err_msg = ''
    file_size = 0
    while byte_counter <= file_size:
        try:
            if file_size == 0:
                file_size = int(data_sock.recv(1024))
                progressbar.update_file_size(file_size)
            data = data_sock.recv(1024)
            if not data:
                break
            file_to_download_to.seek(byte_counter)
            file_to_download_to.write(data)
            byte_counter += len(data)
            queue.put_nowait('bytes {0}'.format(byte_counter))

        except socket.timeout:
            attemps_counter += 1
            read_sockets, write_sockets, error_sockets = select.select([control_sock], [], [])
            if control_sock in read_sockets:
                error = control_sock.recv(1024)
                err_msg = error
                if error.startswith('5'):
                    _close_connection(data_sock, file_to_download_to, queue, control_sock, err_msg)
                    return
            if attemps_counter == 100:
                raise IOError

    _close_connection(data_sock, file_to_download_to, queue, control_sock, err_msg)

from passive_connect import passive_connect


def download_file_by_path(server_path, path_to_store_file, control_sock, session_id, server_ip, group=''):
    """
    Downloads a file in the server by the given server_path. The downloaded file will be saved
    in path_to_store_file path, which sould be a valid path to a file in client's computer.
    If the file exists, it will be overriten, if it does not exists, it will be created.
    """
    file_to_download_to = open(path_to_store_file, 'wb')

    data_sock = passive_connect(control_sock, server_ip)
    if group:
        control_sock.send(' '.join(['GET', server_path, group, 'SESSIONID=' + str(session_id)]))
    else:
        control_sock.send(' '.join(['GET', server_path, 'SESSIONID=' + str(session_id)]))
    while True:
        data = data_sock.recv(1024)
        if not data:
            break
        file_to_download_to.write(data)

    data_sock.close()
    file_to_download_to.close()
    print control_sock.recv(1024)

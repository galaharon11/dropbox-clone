from os import path

from passive_connect import passive_connect


def upload_file_by_path(file_path, server_path, control_sock, session_id, server_ip):
    if(not path.exists(file_path)):
        raise IOError

    data_sock = passive_connect(control_sock, server_ip)

    control_sock.send(' '.join(['APPE', path.join(server_path, path.basename(file_path)),
                                'SESSIONID=' + str(session_id)]))

    file_to_upload = open(file_path, 'rb')
    data_sock.send(file_to_upload.read())
    data_sock.close()
    file_to_upload.close()
    print control_sock.recv(1024)

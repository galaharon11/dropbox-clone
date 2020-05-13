import socket


def passive_connect(control_sock, server_ip):
    control_sock.send('PASV')
    data_port = control_sock.recv(1024)
    if not data_port.startswith('227'):
        print data_port
        raise Exception  # TODO: cahange this

    data_port = int(data_port[data_port.find('PORT ') + 5:])
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.connect((server_ip, data_port))
    return data_sock

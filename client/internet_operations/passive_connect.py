import socket
import tkMessageBox
import os


def passive_connect(control_sock, server_ip):
    try:
        control_sock.send('PASV')
        data_port = control_sock.recv(1024)
        if not data_port.startswith('227'):
            raise Exception

        data_port = int(data_port[data_port.find('PORT ') + 5:])
        data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_sock.connect((server_ip, data_port))
        return data_sock
    except socket.error:
        print 'The action was\'nt completed because the server was terminated. ' \
              'Please make sure the server is running and try again'
        os._exit(0)

class FTPException(Exception):
    def __init__(self):
        self.value = 'FTP error'

    def __str__(self):
        return self.value


class NotImplemented(FTPException):
    def __init__(self):
        self.value = '502 not implemented'
        self.errno = 502


class NeedSessionID(FTPException):
    '''
    This is not a valid FTP error code. On FTP protocol, errno 332 indicates that the user must login in order to
    do an operation. This program does not implements users login on FTP, so errno 332 is overridden.
    In this server, errno 332 means a client must specify a session id in order to continue.
    '''
    def __init__(self):
        self.value = '332 need session id as argument, please specify command again with SESSIONID parameter'
        self.errno = 332


class InvalidSessionID(FTPException):
    '''
    This is not a valid FTP error code. On FTP protocol, errno 430 indicates that the user must login in order to
    do an operation. This program does not implements users login on FTP, so errno 430 is overridden.
    In this server, errno 430 means a client specified an incorrect session id.
    '''
    def __init__(self):
        self.value = '430 Invalid session id, please try again with the correct session id'
        self.errno = 430


class FileAlreadyExists(FTPException):
    '''
    This is not a standard FTP error code.
    '''
    def __init__(self):
        self.value = '505 File or directory already exists on this directory'
        self.errno = 505


class PermissionDenied(FTPException):
    '''
    User is not permitted to do this operation.
    '''
    def __init__(self):
        self.value = '550 permission denied'
        self.errno = 550


class FileDoesNotExists(FTPException):
    '''
    File does not exists on serverl.
    '''
    def __init__(self):
        self.value = '550 File or directory does not exists'
        self.errno = 550


class InternalError(FTPException):
    '''
    Unknown error.
    '''
    def __init__(self):
        self.value = '500 Internal error'
        self.errno = 500


class GroupAlreadyExists(FTPException):
    def __init__(self):
        self.value = '550 Group already exists'
        self.errno = 550


class NoSuchGroup(FTPException):
    def __init__(self):
        self.value = '550 No such group'
        self.errno = 550

class InvalidGroupPassword(FTPException):
    def __init__(self):
        self.value = '430 Invalid password'
        self.errno = 430

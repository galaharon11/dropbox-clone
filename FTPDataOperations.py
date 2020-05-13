def append_file(file_path):
    file_path = command[command.find('APPE ') + 5: command.find(' USERID=')]
    try:
        abs_file_path = self.recieve_file(data_socket, file_path, str(user_id))
        if abs_file_path:
            self.add_file_to_db(abs_file_path, str(user_id), permissions=1)
    except FTPExceptions.FileAlreadyExists as e:
        print e
        complition_queue.put_nowait(str(e))

    if abs_file_path:
        complition_queue.put_nowait("226 Trasfer complete.")
    else:
        complition_queue.put_nowait("500 Internal Error.")  # just a placeholder

def get_file():
    pass

def list_files():
    pass

def append_file():
    pass

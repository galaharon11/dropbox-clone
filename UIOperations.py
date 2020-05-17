import tkFileDialog, tkMessageBox
import os
import threading
import Queue
import time

from internet_operations import upload_file, download_file, list_dir
from components.ProgressBar import ProgressBar


class UIOperations(object):
    def __init__(self, master_window, ftp_control_sock, current_server_path, session_id, server_ip, user_name):
        self.ftp_control_sock = ftp_control_sock
        self.current_server_path = current_server_path
        self.server_ip = server_ip
        self.master_window = master_window
        self.session_id = session_id
        self.user_name = user_name
        self.current_group = ''

    def set_partitaion(self, group):
        if group == 'Shared files':
            group = 'SHARED'
        elif group == 'My files':
            group = ''

        self.current_group = group
        self.current_server_path = '\\'

        self.refresh()

    def refresh(self):
        if self.file_display:
            self.file_display.refresh_display()
            self.control_frame.set_path(self.current_server_path.replace('\\','/'))
            self.control_frame.set_upload_file_button(self.current_group != 'SHARED')
            # Sometimes this funtions sets focus for other widgets
            self.master_window.focus_set()

    def send_command(self, is_group_command, command_name, *params):
        """
        Sends a command to the ftp server.
        :returns: the error string received from the server after sending the command.
        """
        if self.current_group and not is_group_command:
            # Group commands does not accept group parameter.
            params = params + (self.current_group,)
        command = ' '.join([command_name] + list(params) + ['SESSIONID=' + str(self.session_id)])
        self.ftp_control_sock.send(command)
        return self.ftp_control_sock.recv(1024)

    def destroy_progressbar(self, error_msg, show_message_box=True):
        mode = self.progress_bar.mode
        self.progress_bar.destroy()
        if error_msg.startswith('2'):  # 2xx errno is success
            self.refresh()
            if show_message_box:
                tkMessageBox.showinfo(title='Success', message='File {0}ed successfully'.format(mode))
            if self.do_func_when_finish:
                self.do_func_when_finish()
                self.do_func_when_finish = None
        elif error_msg.startswith('550'):
            tkMessageBox.showerror(title='Error', message='You don\'t have the permission to {0} this file'.format(mode))
        elif error_msg.startswith('505'):
            tkMessageBox.showerror(title='Error', message='The file you tried to upload already exists on that directry. '
                                                          'Please delete the file on server, change its name or upload'
                                                          'the file on a different directory')

    def check_if_thread_finished(self, show_message_box):
        if not self.msg_queue.empty():
            msg = self.msg_queue.get_nowait()
            if msg.startswith('bytes'):
                self.progress_bar.set_byte_coutner(int(msg[msg.find(' ') + 1:]))
                self.master_window.after_cancel(self.after_instance)
                self.after_instance = self.master_window.after(100, lambda: self.check_if_thread_finished(show_message_box))
                while not self.msg_queue.empty():
                    msg = self.msg_queue.get_nowait()
                    if not msg.startswith('bytes'):
                        self.destroy_progressbar(msg, show_message_box)
                        self.download_completed = True
                        return
            else:
                self.destroy_progressbar(msg, show_message_box)
                self.download_completed = True

        if not self.download_completed:
            self.after_instance = self.master_window.after(100, lambda: self.check_if_thread_finished(show_message_box))

    def download_from_current_server_path(self, file_name_on_server, file_path_on_client, is_dir=False,
                                          do_func_when_finish=None, show_message_box=True):
        file_path_on_client = file_path_on_client.replace('/','\\')
        file_path_on_server = os.path.join(self.current_server_path, file_name_on_server)

        self.do_func_when_finish = do_func_when_finish
        self.download_completed = False
        self.msg_queue = Queue.Queue()
        self.progress_bar = ProgressBar(self.master_window, 0, file_name_on_server, mode='download')

        download_thread = threading.Thread(target=download_file.download_file_by_path, args=(file_path_on_server,
                                file_path_on_client, self.ftp_control_sock, self.session_id,
                                self.server_ip, self.progress_bar, self.msg_queue, self.current_group))
        self.after_instance = self.master_window.after(100, lambda: self.check_if_thread_finished(show_message_box))
        download_thread.start()


    def upload_from_current_server_path(self):
        file_path = tkFileDialog.askopenfilename(parent=self.master_window , title='Select file')
        if file_path:
            self.download_completed = False
            self.do_func_when_finish = None
            show_message_box = False
            self.msg_queue = Queue.Queue()
            self.progress_bar = ProgressBar(self.master_window, os.stat(file_path).st_size,
                                os.path.basename(file_path), mode='upload')
            upload_thread = threading.Thread(target=upload_file.upload_file_by_path, args=(file_path,
                                self.current_server_path, self.ftp_control_sock, self.session_id,
                                self.server_ip, self.progress_bar, self.msg_queue, self.current_group))
            self.after_instance = self.master_window.after(100, lambda: self.check_if_thread_finished(show_message_box))
            upload_thread.start()

    def add_directory_from_current_directory(self, dir_name):
        error_msg = self.send_command(False, 'MKD', os.path.join(self.current_server_path, dir_name).encode('utf8'))
        if error_msg.startswith('2'):  # 2xx errno is success
            self.refresh()
        else:
            tkMessageBox.showerror(title='Error', message='There is already a file or directory with the same name you entered on this '
                                                          'directory. Please enter a different name.')

    def delete_file_from_current_path(self, name, is_dir):
        if is_dir:
            error_msg = self.send_command(False, 'RMD', os.path.join(self.current_server_path, name))
        else:
            error_msg = self.send_command(False, 'DELE', os.path.join(self.current_server_path, name))

        if error_msg.startswith('2'):  # 2xx errno is success
            self.refresh()
        elif error_msg.startswith('550'): # 550 is permission denied
            tkMessageBox.showerror(title='Error', message='You don\'t have the permission to delete this file.')

    def change_directory(self, directory):
        self.current_server_path = os.path.join(self.current_server_path, directory)
        self.refresh()

    def change_dir_to_parent(self):
        if self.current_server_path != '\\':
            self.current_server_path = os.path.dirname(self.current_server_path)
            self.refresh()

    def rename_file_in_current_path(self, file_name, new_file_name):
        error_msg = self.send_command(False, 'RNTO', os.path.join(self.current_server_path, file_name),
                                              os.path.join(self.current_server_path, new_file_name))
        print error_msg
        if error_msg.startswith('2'):  # 2xx errno is success
            self.refresh()
        elif error_msg.startswith('550'): # 550 is permission denied
            tkMessageBox.showerror(title='Error', message='You don\'t have the permission to rename this file.')
        elif error_msg.startswith('505'): # 550 is permission denied
            tkMessageBox.showerror(title='Error', message='There is already a file or directory with the same name you entered on this '
                                                          'directory. Please enter a different name.')

    def update_compenents(self, file_display=None, control_frame=None, groups_view=None):
        """
        Add a FileDisplay to be associated with this class to. file_display must be loaded with this function
        for some functions to work properly.
        """
        self.file_display = file_display
        self.control_frame = control_frame
        self.groups_view = groups_view

    def get_current_path(self):
        return self.current_server_path

    def list_files_in_current_dir(self):
        return list_dir.list_directory_by_path(self.current_server_path, self.session_id,
                                               self.ftp_control_sock, self.server_ip, self.current_group)

    def recursive_list(self, directory):
        """
        The function will iterate recursively and return a touple that contains a list of directories as first element
        and a list of files as second element.
        """
        file_list = []
        dir_list = []
        self._recursive_list(os.path.join(self.current_server_path, directory), file_list, dir_list)
        return dir_list, file_list

    def _recursive_list(self, path, file_list, dir_list):
        files, dirs = list_dir.list_directory_by_path(path, self.session_id,
                                                      self.ftp_control_sock, self.server_ip, self.current_group)
        file_list += map(lambda f: os.path.join(path, f), files)
        dir_list += map(lambda d: os.path.join(path, d), dirs)
        for directory in dirs:
            self._recursive_list(os.path.join(path, directory), file_list, dir_list)

    def share_file_from_current_dir(self, file_name, user_name, permissions):
        error_msg = self.send_command(False, 'SHAR', os.path.join(self.current_server_path, file_name),
                                      user_name, str(permissions))
        print error_msg
        if error_msg.startswith('2'):  # 2xx errno is success
            tkMessageBox.showinfo(title='Success', message='File shared successfully')
            self.refresh()
            return True  # success
        elif error_msg.startswith('550'):  # 550 is permission denied
            tkMessageBox.showerror(title='Error', message='You don\'t have the permission to share this file.')
        else:
            tkMessageBox.showerror(title='Error', message='User {0} does not exists.'.format(user_name))

        return False

    def group_get(self):
        msg = self.send_command(True, 'GROUP', 'GET')
        if msg.startswith('2'):
            print msg
            if len(msg) == 3:
                return []
            elif ',' in msg:
                return msg[4:].split(',')
            else:
                return [msg[4:]]

    def group_create(self, group_name, group_pass):
        msg = self.send_command(True, 'GROUP', 'CREATE', group_name, group_pass)
        if not msg.startswith('2'):
            tkMessageBox.showerror(title='Error', message='A group with this name already exists, please enter a new group name.')
            return False
        return True

    def group_join(self, group_name, group_pass):
        if group_name not in self.groups_view.groups:
            msg = self.send_command(True, 'GROUP', 'JOIN', group_name, group_pass)
            if not msg.startswith('2'):
                if msg.startswith('550'):
                    tkMessageBox.showerror(title='Error', message='A group with this name does not exists.')
                    return False
                elif msg.startswith('430'):
                    tkMessageBox.showerror(title='Error', message='Incorrect password.')
                    return False
            return True
        else:
            tkMessageBox.showerror(title='Error', message='You are in group "{0}" already.'.format(group_name))
            return False

import Tkinter as tk
import os
import tkMessageBox
from shutil import rmtree

class ResetView(tk.Frame):
    def reset_server(self, event):
        answer = tkMessageBox.askyesno(title='Warning', message='Are you sure that you want to reset this server? All users'
                                                                ', files, groups and logs will be lost')
        if answer:
            files_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.path_to_files)
            rmtree(files_path)

            self.server_db.close()
            os.remove(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'server.db'))

            os._exit(0)

    def __init__(self, parent, server_db, path_to_files):
        """
        A frame for reset view.
        Reset view contains a button that will reset the server.
        """
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.path_to_files = path_to_files
        self.server_db = server_db

        reset_button = tk.Button(self, text='Reset this server', width=15, highlightthickness=0)
        reset_button.pack(side='top', padx=10, pady=10)
        reset_button.bind('<Button-1>', self.reset_server)
        self.focus_set()

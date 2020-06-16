import Tkinter as tk
import ttk
import tkFont
import os

from GenericAdminView import GenericAdminView
from ResetView import ResetView


class AdminWindow(tk.Tk):
    def __init__(self, server_db, logger, path_to_files):
        tk.Tk.__init__(self)
        self.title('Admin mode')
        self.geometry('700x700+200+20')
        self.minsize(700, 600)
        path_to_files = os.path.join(os.path.dirname(os.path.dirname(__file__)), path_to_files)

        tabs = ttk.Notebook(self)
        tabs.add(GenericAdminView(self, 'user', server_db, logger, path_to_files), text='Users')
        tabs.add(GenericAdminView(self, 'group', server_db, logger, path_to_files), text='Groups')
        tabs.add(GenericAdminView(self, 'file', server_db, logger, path_to_files), text='Files')
        tabs.add(GenericAdminView(self, 'error', server_db, logger, path_to_files), text='Errors')
        tabs.add(ResetView(self, server_db, path_to_files), text='Reset server')
        tabs.pack(fill='both', expand=True)
        try:
            self.mainloop()
        except KeyboardInterrupt:
            exit()

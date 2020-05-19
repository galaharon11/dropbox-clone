import Tkinter as tk
import ttk
import tkFont
import os

from FTP.FTPDatabaseOperations import get_all_users, get_all_groups, get_all_files


class GenericAdminView(tk.Frame):
    def disable_resize(self, event):
        # disable tree_view resizing
        if self.tree_view.identify_region(event.x, event.y) == 'separator':
            return 'break'

    def _get_dir_size(self, path):
        total_size = 0
        if os.path.exists(path):
            if os.path.isdir(path):
                for files in os.walk(path):
                    for f in files[2]:
                        file_to_check = os.path.join(files[0], f)
                        total_size += os.stat(file_to_check).st_size
            else:
                total_size = os.stat(path).st_size
        else:
            return '0 Bytes'

        if total_size >= 1024**2:
            return '{:.2f} MB'.format(total_size / float(1024**2))
        elif total_size >= 1024:
            return '{:.2f} KB'.format(total_size / float(1024))
        else:
            return '{0} Bytes'.format(total_size)


    def _log_scroll(self, *args):
        self.timestemp_listbox.yview(*args)
        self.logs_listbox.yview(*args)

    def show_log(self, event):
        log_frame = tk.Toplevel(self.parent)
        log_frame.geometry('600x700+300+40')
        log_frame.minsize(500, 500)
        listbox_wrap_frame = tk.Frame(log_frame, background='white')

        listbox_wrap_frame.grid_columnconfigure(1, weight=1)
        listbox_wrap_frame.grid_rowconfigure(0, weight=1)

        scroller = tk.Scrollbar(listbox_wrap_frame, orient='vertical')
        scroller.grid(column=2, row=0, sticky='ns')
        self.logs_listbox = tk.Listbox(listbox_wrap_frame, background='white', selectmode='single',
                                  highlightthickness=0, activestyle='none')
        logs = self.logger.get_logs(operation_type=self.view)
        for log in logs:
            self.logs_listbox.insert('end', log[0])

        self.logs_listbox.pack(side='top', fill='both', expand=True)

        timesteps = tk.Listbox(listbox_wrap_frame, background='white', selectmode='single',
                                  highlightthickness=0, activestyle='none')

        self.timestemp_listbox = tk.Listbox(listbox_wrap_frame, background='white', selectmode='single',
                                  highlightthickness=0, activestyle='none')
        for log in logs:
            self.timestemp_listbox.insert('end', log[1])

        self.timestemp_listbox.grid(column=0, row=0, sticky='nswe')
        self.logs_listbox.grid(column=1, row=0, sticky='nswe')

        self.logs_listbox.configure(yscrollcommand=scroller.set)
        self.timestemp_listbox.configure(yscrollcommand=scroller.set)
        scroller.configure(command=self._log_scroll)

        listbox_wrap_frame.grid(column=0, row=0, sticky='nswe', padx=10, pady=10)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

    def __init__(self, parent, view, server_db, logger, path_to_files):
        """
        Generic view for admin. It can show three deferent views, according to 'view' parameter:
        'user' - show a list of users and users log.
        'file' - show a list of files and files log.
        'group' - show a list of groups and groups log.
        'error' - show a button that will shwo a list of error logs.
        """
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.server_db = server_db
        self.logger = logger
        self.view = view
        if view != 'error':
            description = tk.Label(self, text='A list of all {0}s:'.format(view))
            description.pack(side='top', padx=10, pady=(10,5))

            if view == 'file':
                self.tree_view = ttk.Treeview(self, columns=('name', 'size', 'owner'), show='headings')
                self.tree_view.column('name', width=300, minwidth=300, stretch=False)
                self.tree_view.column('size', width=100, minwidth=100, stretch=False)
                self.tree_view.column('owner', width=150, minwidth=150, stretch=False)
                self.tree_view.heading('owner', text='Owner of this file', anchor='w')
                self.tree_view.heading('name', text='File path', anchor='w')
                self.tree_view.heading('size', text='Files size', anchor='w')

            else:
                self.tree_view = ttk.Treeview(self, columns=('name', 'size'), show='headings')

                self.tree_view.column('name', width=200, minwidth=200, stretch=False)
                self.tree_view.column('size', width=100, minwidth=100, stretch=False)

                if view == 'user':
                    self.tree_view.heading('name', text='User name', anchor='w')
                elif view == 'group':
                    self.tree_view.heading('name', text='Group name', anchor='w')
                self.tree_view.heading('size', text='Total files size', anchor='w')

            if view == 'user':
                users_list = get_all_users(self.server_db)
                for i in range(len(users_list)):
                    username, user_id = users_list[i]
                    path = os.path.join(path_to_files, str(user_id))
                    size = self._get_dir_size(path)
                    self.tree_view.insert('', i, None, values=(username, size))

            elif view == 'file':
                files_dict = get_all_files(self.server_db)
                i = 0
                for file_path, owner in files_dict.items():
                    size = self._get_dir_size(file_path)
                    self.tree_view.insert('', i, None, values=(file_path, size, owner))
                    i += 1

            elif view == 'group':
                groups_list = get_all_groups(self.server_db)
                for i in range(len(groups_list)):
                    group_name, group_id = groups_list[i]
                    path = os.path.join(path_to_files, 'g' + str(group_id))
                    size = self._get_dir_size(path)
                    self.tree_view.insert('', i, None, values=(group_name, size))

            vsb = tk.Scrollbar(self.tree_view, orient="vertical", command=self.tree_view.yview)
            vsb.pack(side='right', fill='y')
            self.tree_view.configure(yscrollcommand=vsb.set)

            self.tree_view.pack(side='left', padx=10, pady=(10,20), fill='both', expand=True)

            self.tree_view.bind("<Button-1>", self.disable_resize)
            self.tree_view.bind("<Motion>", self.disable_resize)

            show_log_btn = tk.Button(self, text='Show {0} logs'.format(view), width=15)
            show_log_btn.pack(side='right', padx=10)
        else:
            show_log_btn = tk.Button(self, text='Show error logs', width=15, highlightthickness=0)
            show_log_btn.pack(side='top', padx=10, pady=10)
            self.focus_set()

        show_log_btn.bind('<Button-1>', self.show_log)

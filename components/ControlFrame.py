import Tkinter as tk
import tkSimpleDialog
from PIL import Image, ImageTk
import os


class ControlFrame(tk.Frame):
    def set_path(self, path):
        self.address_bar.delete(0, 'end')
        self.address_bar.insert(0, path)

    def set_search_text(self):
        if self.search_bar.get() == '':
            self.search_bar.insert(0, 'Search')
            self.search_bar.configure(foreground='grey')

    def search_entry_pressed(self):
        if self.search_bar['foreground'] == 'grey':
            self.search_bar.delete(0, 'end')
            self.search_bar.configure(foreground='black')

        self.file_display.unmark_all_file_labels()

    def search_typed(self, event):
        if event.keycode == 8:  # Delete pressed
            search_string = self.search_bar.get()[:-1]
        elif event.char:
            search_string = self.search_bar.get() + event.char
        else:
            return

        if search_string:
            found_files = []
            found_dirs = []
            for file_label in self.file_display.file_labels:
                if(search_string in file_label.file_name):
                    found_files.append(file_label.file_name)

            for dir_label in self.file_display.dir_labels:
                if(search_string in dir_label.file_name):
                    found_dirs.append(dir_label.file_name)
            self.file_display.filter_display(found_files, found_dirs)
        else:
            self.file_display.retrieve_display()

    def add_dir_dialog(self):
        dir_name = tkSimpleDialog.askstring('Add a directory',
                             'Please enter the name of the directory you want to add', parent=self.parent)
        if dir_name:
            self.ui_operations.add_directory_from_current_directory(dir_name)

    def manage_group(self):
        pass

    def set_mode(self, mode):
        """
        mode is one of the following strings:
        'default' - Default state. 'Upload a file' and 'Add new directory' both active.
        'shared' - Shared files - Same as default but 'Upload a file' button is disabled.
        'group' - Group files - Same as default but 'Manage group' button is added.
        """
        self.upload_file_button.pack_forget()
        self.add_dir_button.pack_forget()
        self.manage_group_button.pack_forget()
        if mode == 'group':
            self.upload_file_button.pack(side='left', padx=70)
            self.add_dir_button.pack(side='left', padx=70)
            self.manage_group_button.pack(side='right', padx=70)
        else:
            self.upload_file_button.pack(side='right', padx=100)
            self.add_dir_button.pack(side='left', padx=100)

        state = 'disabled' if mode == 'shared' else 'normal'
        self.upload_file_button.configure(state=state)

    def __init__(self, parent, file_display, ui_operations):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.file_display = file_display
        self.ui_operations = ui_operations

        self.addr_frame = tk.Frame(self)
        self.search_bar = tk.Entry(self.addr_frame, foreground='grey')
        self.search_bar.pack(side='right', ipady=3, ipadx=3, padx=(10, 0))
        self.search_bar.insert(0, 'Search')
        self.search_bar.bind("<Button-1>", lambda event: self.search_entry_pressed())
        self.search_bar.bind("<Key>", lambda event: self.search_typed(event))

        self.address_bar = tk.Entry(self.addr_frame)
        self.address_bar.insert(0, '/')
        self.address_bar.pack(side='right', expand=True, fill='both', ipady=3, ipadx=3)

        up_arrow_image = Image.open(os.path.join(os.path.dirname(__file__), 'icons', 'up.png')).convert('RGBA')
        up_arorw_icon = ImageTk.PhotoImage(up_arrow_image)
        self.return_button = tk.Button(self.addr_frame, image=up_arorw_icon,
                                       command=self.ui_operations.change_dir_to_parent)
        self.return_button.image = up_arorw_icon
        self.return_button.pack(side='left', padx=(0, 10))
        self.addr_frame.pack(side='top', expand=True, fill='both')

        self.operations_frame = tk.Frame(self)
        self.upload_file_button = tk.Button(self.operations_frame, text='Upload a file',
                                         command=self.ui_operations.upload_from_current_server_path)
        self.upload_file_button.pack(side='right', padx=100)
        self.add_dir_button = tk.Button(self.operations_frame, text='Add new directory',
                                        command=self.add_dir_dialog)
        self.add_dir_button.pack(side='left', padx=100)

        self.operations_frame.pack(side='bottom', pady=10, expand=True)

        self.manage_group_button = tk.Button(self.operations_frame, text='Manage group',
                                             command=self.manage_group)

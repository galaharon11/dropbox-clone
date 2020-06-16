import Tkinter as tk
import os
from PIL import ImageTk
import threading
import random
import string
import tkSimpleDialog
import tkMessageBox

from ShareDialog import ShareDialog


class FileLabel(tk.Label):
    ICON_SIZE = 82
    MAX_FILENAME_LENGTH = 13
    number_of_columns = 9

    def share_file(self):
        ShareDialog(self.file_view_parent, self.ui_operations, self.file_name, self.is_dir)

    def rename_file(self):
        new_name = tkSimpleDialog.askstring('Rename this file',
                             'Please enter the new name of this file', parent=self.file_view_parent)
        if new_name:
            if self.ui_operations.filter_file_name(new_name):
                self.ui_operations.rename_file_in_current_path(self.file_name, new_name)
            else:
                tkMessageBox.showerror('Error', 'Your files contains illegal characters')

    def start_file(self, tmp_file_path):
        try:
            os.startfile(tmp_file_path)
        except WindowsError:
            pass

    def file_open(self):
        self.file_view_parent.unmark_all_file_labels()
        if not self.file_view_parent.is_ctrl_pressed:
            if not self.is_dir:
                # generate a random temp filename
                tmp_file_name = ''.join(random.choice(string.ascii_lowercase) for i in range(12)) + self.file_extension
                tmp_dir = os.path.join(os.path.realpath('.'), 'tmp')
                if not os.path.exists(tmp_dir):
                    os.mkdir(tmp_dir)

                tmp_file_path = os.path.join(tmp_dir, tmp_file_name)
                open(tmp_file_path, 'w').close()  # Create temp file
                self.ui_operations.download_from_current_server_path(self.file_name,
                    tmp_file_path, do_func_when_finish=lambda: self.start_file(tmp_file_path))
            else:
                self.ui_operations.change_directory(self.file_name)

    def add_image(self, image):
        self.image = ImageTk.PhotoImage(image)
        self.configure(image=self.image, text=self.short_filename)

    def popup_menu_show(self, event):
        self.file_view_parent.mark_file_label(self, right_mouse_pressed=True)
        if len(self.file_view_parent.marked_labels) > 1:
            self.group_popup_menu.tk_popup(event.x_root, event.y_root)
        else:
            self.popup_menu.tk_popup(event.x_root, event.y_root)

    def mouse_hover(self):
        # Hover if the label is not marked
        if(self not in self.file_view_parent.marked_labels):
            self.config(bg='#ddeeff')

    def mouse_unhover(self):
        # Unhover if the label is not marked
        if(self not in self.file_view_parent.marked_labels):
            self.config(bg='white')

    def do_grid(self, file_number, number_of_columns):
        self.grid(padx=2, pady=5, row=file_number // number_of_columns,
                  column=file_number % number_of_columns)

    def __init__(self, frame_parent, file_view_parent, file_name, file_number, ui_operations, is_dir=False):
        tk.Label.__init__(self, frame_parent, background='white', compound='top')
        self.file_view_parent = file_view_parent
        self.is_dir = is_dir
        self.file_name = file_name
        self.ui_operations = ui_operations

        try:
            self.file_extension = file_name[file_name.rindex('.'):]
        except ValueError:
            self.file_extension = ''

        if(len(file_name) > FileLabel.MAX_FILENAME_LENGTH):
            self.short_filename = file_name[:FileLabel.MAX_FILENAME_LENGTH - 3] + '...'
        else:
            self.short_filename = file_name

        self.bind("<Double-Button-1>", lambda event: self.file_open())
        self.bind("<Button-1>", lambda event: self.file_view_parent.mark_file_label(self))
        self.bind("<Enter>", lambda event: self.mouse_hover())
        self.bind("<Leave>", lambda event: self.mouse_unhover())


        # this popup menu will be available when multiple files are marked by the user
        self.group_popup_menu = tk.Menu(self.file_view_parent, tearoff=0)
        self.group_popup_menu.add_command(label="Download", command=self.file_view_parent.download_marked_files)
        self.group_popup_menu.add_command(label="Delete", command=self.file_view_parent.remove_marked_files)

        # this popup menu will be available when only one file is marked by the user
        self.popup_menu = tk.Menu(self.file_view_parent, tearoff=0)
        self.popup_menu.add_command(label="Open", command=self.file_open)
        self.popup_menu.add_command(label="Download", command=self.file_view_parent.download_marked_files)
        self.popup_menu.add_command(label="Rename", command=self.rename_file)
        if not self.is_dir:
            self.popup_menu.add_separator()
            self.popup_menu.add_command(label="Share", command=self.share_file)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label="Delete", command=self.file_view_parent.remove_marked_files)
        self.bind("<Button-3>", lambda event: self.popup_menu_show(event))

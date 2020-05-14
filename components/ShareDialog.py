import Tkinter as tk
import tkMessageBox
import tkFont

from PermissionsConsts import *


class ShareDialog(tk.Toplevel):
    def button_pressed(self):
        permissions = self.permission_download_var | self.permission_delete_var | self.permission_rename_var | \
                      self.permission_edit_var
        permissions |= DIRECTORY if self.is_dir else 0
        if (not self.ui_operations.share_file_from_current_dir(self.file_name_to_share,
            self.nameEntry.get(), permissions)):
            tkMessageBox.showerror(title='Error', message='user {0} does not exists'.format(self.nameEntry.get()))

    def __init__(self, parent, ui_operations, file_name_to_share, is_dir=False):
        tk.Toplevel.__init__(self, parent)
        self.title('Enter user name')
        self.resizable(False, False)
        self.ui_operations = ui_operations
        self.file_name_to_share = file_name_to_share
        self.is_dir = is_dir

        default_font = tkFont.nametofont("TkTextFont")
        text_font = default_font.copy()
        text_font.configure(size=12)

        dir_or_file_string = 'directory' if is_dir else 'file'
        self.nameLabel = tk.Label(self, font=text_font, text='Please enter the username of the person you want '
                                             'to share this {0} with'.format(dir_or_file_string))
        self.nameLabel.grid(row=0, column=0, columnspan=2, pady=5, padx=20, sticky='we')
        self.nameEntry = tk.Entry(self)
        self.nameEntry.grid(row=1, column=0, columnspan=2, pady=5, padx=20, sticky='we')

        self.permission_label = tk.Label(self, font=text_font, text='What will that user be able to do with this {0}?'
                                         .format(dir_or_file_string))
        self.permission_label.grid(row=2, column=0, pady=5, padx=20, sticky='w')

        self.permission_download_var = tk.IntVar()
        self.permission_delete_var = tk.IntVar()
        self.permission_rename_var = tk.IntVar()
        self.permission_edit_var = tk.IntVar()

        self.permission_download = tk.Checkbutton(self, font=text_font, text='Download it',
                                   variable=self.permission_download_var, onvalue=1, offvalue=DOWNLOAD)
        self.permission_download.grid(row=3, column=0, padx=20, sticky='w')
        self.permission_delete = tk.Checkbutton(self, font=text_font, text='Delete it',
                                 variable=self.permission_delete_var, onvalue=1, offvalue=DELETE)
        self.permission_delete.grid(row=4, column=0, padx=20, sticky='w')
        self.permission_rename = tk.Checkbutton(self, font=text_font, text='Rename it',
                                 variable=self.permission_rename_var, onvalue=1, offvalue=RENAME)
        self.permission_rename.grid(row=5, column=0, padx=20, sticky='w')
        self.permission_edit = tk.Checkbutton(self, font=text_font, text='Edit it',
                               variable=self.permission_edit_var, onvalue=1, offvalue=DIR_EDIT)
        if is_dir:
            self.permission_edit.grid(row=6, column=0, padx=20, sticky='w',
                                    variable=self.permission_download_var)

        self.send_button = tk.Button(self, font=text_font, text='share', command=self.button_pressed)
        self.send_button.grid(row=7, column=0, columnspan=2, pady=(5,15))

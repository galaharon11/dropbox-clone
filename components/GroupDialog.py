import Tkinter as tk
import tkMessageBox


class GroupDialog(tk.Toplevel):
    def action(self):
        group_name = self.name_entry.get()
        group_pass = self.password_entry.get()
        if(not (group_name.isalnum() and group_pass.isalnum() \
             and all(ord(c) < 128 for c in group_name+group_pass))):
            tkMessageBox.showerror(title='Error', message='Group name and password '
                                                         'must contain english letters and numbers only')
            return

        if group_name and group_pass:
            if self.mode == 'create':
                success = self.ui_operations.group_create(group_name, group_pass)
            elif self.mode == 'join':
                success = self.ui_operations.group_join(group_name, group_pass)
            if success:
                self.parent.refresh()
                self.destroy()
        else:
            tkMessageBox.showinfo(title='Add info', message='Please enter group name and password')


    def __init__(self, parent, ui_operations, mode='create'):
        """
        mode: 'create' or 'join'
        """
        tk.Toplevel.__init__(self, parent)
        self.resizable(False, False)
        self.geometry("+250+130")
        self.title('{0} a group'.format(mode).capitalize())
        self.parent = parent
        self.mode = mode
        self.ui_operations = ui_operations

        self.text_label = tk.Label(self, text='Enter the name and the password of the group')
        self.text_label.grid(column=0, row=0, pady=5, padx=10, columnspan=2)

        self.name_label = tk.Label(self, text="Group name:")
        self.name_entry = tk.Entry(self)
        self.name_entry.grid(column=1, row=1, pady=5, padx=10)
        self.name_label.grid(column=0, row=1, pady=5, padx=10)

        self.password_label = tk.Label(self, text="Group password:")
        self.password_entry = tk.Entry(self, show='*')
        self.password_entry.grid(column=1, row=2, padx=10)
        self.password_label.grid(column=0, row=2, padx=10)

        self.login_button = tk.Button(self, text='{0}'.format(mode), command=self.action)
        self.login_button.grid(column=0, row=3, columnspan=2, pady=5, padx=10)

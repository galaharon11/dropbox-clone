import Tkinter as tk
import tkMessageBox
import tkFont


class ManageGroupWindow(tk.Toplevel):
    def leave_group(self):
        answer = tkMessageBox.askyesno('Are you sure?', 'Are you sure that you want to leave the group {0}'
                                                        .format(self.group_name))
        if answer:
            self.ui_operations.remove_this_user_from_group(self.group_name)
            self.ui_operations.refresh(change_to_my_files=True)
            self.destroy()

    def delete_group(self):
        answer = tkMessageBox.askyesno('Are you sure?', 'Are you sure that you want to delete the group {0}'
                                                        .format(self.group_name))
        if answer:
            self.ui_operations.delete_group(self.group_name)
            self.ui_operations.refresh(change_to_my_files=True)
            self.destroy()

    def kick_user(self, event):
        if self.is_owner:
            user = self.names_listbox.get(tk.ACTIVE)
            if user == self.ui_operations.user_name:
                answer = tkMessageBox.showerror('Error', 'You cannot remove yourself from the group.')
                return
            answer = tkMessageBox.askyesno('Are you sure?', 'Are you sure that you want to remove user '
                                                           '{0} from the group {1}?'.format(user, self.group_name))
            if answer:
                self.ui_operations.remove_user_from_group(self.group_name, user)
                self.refresh()

    def refresh(self):
        self.users = self.ui_operations.get_users_in_group(self.group_name)
        print self.users
        self.names_listbox.delete(0, 'end')
        for user in self.users:
            self.names_listbox.insert('end', user)

    def __init__(self, parent, ui_operations):
        tk.Toplevel.__init__(self, parent)
        self.title('Manage group')
        self.parent = parent
        self.ui_operations = ui_operations
        self.group_name = self.ui_operations.current_group

        self.users = self.ui_operations.get_users_in_group(self.group_name)
        print self.users
        self.is_owner = self.ui_operations.user_name == self.users[0]

        default_font = tkFont.nametofont("TkTextFont")
        managegroup_font = default_font.copy()
        managegroup_font.configure(size=14)

        self.description1 = tk.Label(self, text='This is a list of users in group {0}.'
                                        .format(self.group_name), font=managegroup_font)
        self.description1.pack(side='top', pady=3, padx=20)
        if self.is_owner:
            self.description2 = tk.Label(self, text='You are the owner of this group. '
                                    'Double click on a user to remove him from the group', font=managegroup_font)
            self.description2.pack(side='top', pady=3, padx=20)

        self.listbox_wrap_frame = tk.Frame(self, background='white', borderwidth=1)
        self.scroller = tk.Scrollbar(self.listbox_wrap_frame, orient='vertical')
        self.scroller.pack(side='right', fill='y')
        self.names_listbox = tk.Listbox(self.listbox_wrap_frame, background='white', selectmode='single',
                                  highlightthickness=0, activestyle='none', borderwidth=0, font=managegroup_font)
        for user in self.users:
            self.names_listbox.insert('end', user)

        self.names_listbox.configure(yscrollcommand=self.scroller.set)
        self.scroller.configure(command=self.names_listbox.yview)

        self.names_listbox.pack()
        self.listbox_wrap_frame.pack(side='top', padx=20, pady=10)

        self.names_listbox.bind('<Double-Button-1>', self.kick_user)

        if self.is_owner:
            self.leave_group_btn = tk.Button(self, text='Delete this group', command=self.delete_group, font=managegroup_font)
        else:
            self.leave_group_btn = tk.Button(self, text='Leave this group', command=self.leave_group, font=managegroup_font)

        self.leave_group_btn.pack(side='bottom', padx=20, pady=10)

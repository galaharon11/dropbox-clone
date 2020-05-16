import Tkinter as tk
import tkFont
import tkSimpleDialog

class GroupsView(tk.Listbox):
    def create_group(self):
        group_name = tkSimpleDialog.askstring('Create a group', 'Enter the name of the group')
        if group_name:
            self.ui_operations.group_create(group_name)
            self.refresh()

    def join_group(self):
        group_name = tkSimpleDialog.askstring('Join a group', 'Enter the name of the group')
        if group_name:
            self.ui_operations.group_join(group_name)
            self.refresh()

    def listbox_pressed(self, event):
        self.ui_operations.set_partitaion(self.get(tk.ACTIVE))

    def refresh(self):
        self.groups = ['My files', 'Shared files'] + self.ui_operations.group_get()
        self.delete(0,'end')
        for group in self.groups:
            self.insert('end', group)

    def __init__(self, parent, ui_operations, groups=[]):
        tk.Listbox.__init__(self, parent, background='white', selectmode='single', highlightthickness=0, activestyle='none')
        self.parent = parent
        self.ui_operations = ui_operations

        default_font = tkFont.nametofont("TkTextFont")
        groupview_font = default_font.copy()
        groupview_font.configure(size=14)
        self.configure(font=groupview_font)
        self.groups = ['My files', 'Shared files'] + groups
        for group in self.groups:
            self.insert('end', group)

        create_group_btn = tk.Button(self, text='Create a group', command=self.create_group, font=groupview_font)
        create_group_btn.pack(side='bottom', fill='x')
        join_group_btn = tk.Button(self, text='Join a group', command=self.join_group, font=groupview_font)
        join_group_btn.pack(side='bottom', fill='x')

        self.bind('<Double-Button-1>', self.listbox_pressed)

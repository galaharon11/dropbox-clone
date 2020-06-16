import Tkinter as tk
import tkFont
import tkSimpleDialog

from GroupDialog import GroupDialog


class GroupsView(tk.Frame):
    def listbox_pressed(self, event):
        self.ui_operations.set_partitaion(self.listbox.get(tk.ACTIVE))

    def refresh(self):
        self.groups = ['My files', 'Shared files'] + self.ui_operations.group_get()
        self.listbox.delete(0, 'end')
        for group in self.groups:
            self.listbox.insert('end', group)

    def __init__(self, parent, ui_operations):
        tk.Frame.__init__(self, parent, background='white')

        self.listbox_wrap_frame = tk.Frame(self, background='white', borderwidth=1)
        self.scroller = tk.Scrollbar(self.listbox_wrap_frame, orient='vertical')
        self.scroller.pack(side='right', fill='y')
        self.listbox = tk.Listbox(self.listbox_wrap_frame, background='white', selectmode='single',
                                  highlightthickness=0, activestyle='none', borderwidth=0)

        self.parent = parent
        self.ui_operations = ui_operations

        default_font = tkFont.nametofont("TkTextFont")
        groupview_font = default_font.copy()
        groupview_font.configure(size=14)
        self.listbox.configure(font=groupview_font)
        self.groups = ['My files', 'Shared files'] + self.ui_operations.group_get()
        for group in self.groups:
            self.listbox.insert('end', group)

        create_group_btn = tk.Button(self, text='Create a group', command=lambda: GroupDialog(self,
                                     self.ui_operations, mode='create'), font=groupview_font)
        create_group_btn.pack(side='bottom', fill='x')

        join_group_btn = tk.Button(self, text='Join a group', command=lambda: GroupDialog(self,
                                   self.ui_operations, mode='join'), font=groupview_font)
        join_group_btn.pack(side='bottom', fill='x')

        self.listbox.pack(side='top', fill='y', padx=10, expand=True)

        self.listbox.configure(yscrollcommand=self.scroller.set)
        self.scroller.configure(command=self.listbox.yview)

        self.listbox_wrap_frame.pack(side='top', fill='y', expand=True)
        self.listbox.bind('<Double-Button-1>', self.listbox_pressed)

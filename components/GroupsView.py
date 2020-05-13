import Tkinter as tk
import tkFont

class GroupsView(tk.Listbox):

    def pressed(self, event):
        self.ui_operations.set_partitaion(self.get(tk.ACTIVE))

    def __init__(self, parent, ui_operations, groups=[]):
        tk.Listbox.__init__(self, parent, background='white', selectmode='single', highlightthickness=0, activestyle='none')
        self.parent = parent
        self.ui_operations = ui_operations

        default_font = tkFont.nametofont("TkTextFont")
        listbox_font = default_font.copy()
        listbox_font.configure(size=14)
        self.configure(font=listbox_font)
        self.groups = ['My files', 'Shared files'] + groups
        for group in self.groups:
            self.insert('end', group)

        self.bind('<Double-Button-1>', self.pressed)

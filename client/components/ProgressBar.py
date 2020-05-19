import Tkinter as tk
import ttk
import tkMessageBox

class ProgressBar(tk.Toplevel):
    def __init__(self, parent, file_size, file_name, mode='upload'):
        tk.Toplevel.__init__(self, parent)
        self.file_size = file_size
        self.file_name = file_name
        self.mode = mode
        self.byte_counter = 0

        try:
            label = tk.Label(self, text=u'{0}ing file: {1}'.format(mode, file_name))
        except UnicodeDecodeError:
            label = tk.Label(self, text=u'{0}ing file'.format(mode))

        label.pack(side='top', padx=20, pady=10)
        self.progressbar_val = tk.IntVar()
        self.progressbar = ttk.Progressbar(self, orient='horizontal', length=300,
                                           mode='determinate', variable=self.progressbar_val)
        self.progressbar.pack(side='bottom', pady=10, padx=20)

    def update_file_size(self, file_size):
        self.file_size = file_size

    def set_byte_coutner(self, byte_counter):
        self.byte_counter = byte_counter
        self.progressbar_val.set(int((self.byte_counter / float(self.file_size) * 100)))

import Tkinter as tk
import subprocess
import os
import traceback
from PIL import Image
import tkFileDialog

from FileLabel import FileLabel


class FileDisplay(tk.Canvas):
    def _add_file_labels(self, file_names, dir_names=[]):
        extensions = set()
        for dir_name_to_add in dir_names:
            dir_label = FileLabel(self.files_frame, self, dir_name_to_add, self._num_of_files,
                                  self.ui_operations, is_dir=True)
            extensions.add('directory')
            self.dir_labels.append(dir_label)
            self._num_of_files += 1

        for file_name_to_add in file_names:
            file_label = FileLabel(self.files_frame, self, file_name_to_add, self._num_of_files, self.ui_operations)
            extensions.add(file_label.file_extension[1:])
            self.file_labels.append(file_label)
            self._num_of_files += 1

        icon_dir_path = os.path.join(os.path.dirname(__file__), 'icons')
        images = self.get_icon_for_extensions(icon_dir_path, list(extensions))

        for dir_label in self.dir_labels:
            dir_label.add_image(images['directory'])

        for file_label in self.file_labels:
            file_label.add_image(images[file_label.file_extension[1:]])

    def get_icon_for_extensions(self, path, extensions):
        """
        :param: extensions: list of strings, each string is an extension (['txt','exe','docx'])
        :returns: a dict with key as extension and Image object as value
        """
        try:
            get_icon_exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'GetIcon.exe'))
            subprocess.check_output([get_icon_exe_path, str(FileLabel.ICON_SIZE), path] + extensions).split('\n')
            images = {}
            for extension in extensions:
                images[extension] = Image.open(os.path.join(path, extension + '.ico')).convert('RGBA')

            return images
        except:
            traceback.print_exc()

    def filter_display(self, file_names, dir_names=[]):
        for x in self.currently_on_screen:
            x.grid_forget()

        self.currently_on_screen = []
        self._num_of_files = 0

        dir_labels = filter(lambda x: x.file_name in dir_names, self.dir_labels)
        file_labels = filter(lambda x: x.file_name in file_names, self.file_labels)
        for dir_name_to_add in dir_labels:
            dir_name_to_add.do_grid(self._num_of_files)
            self.currently_on_screen.append(dir_name_to_add)
            self._num_of_files += 1
        for file_name_to_add in file_labels:
            file_name_to_add.do_grid(self._num_of_files)
            self.currently_on_screen.append(file_name_to_add)
            self._num_of_files += 1

    def retrieve_display(self):
        self.filter_display([label.file_name for label in self.file_labels],
                            [label.file_name for label in self.dir_labels])

    def onFrameConfigure(self):
        '''Reset the scroll region to encompass the inner frame'''
        self.configure(scrollregion=self.bbox("all"))

    def unmark_all_file_labels(self):
        for marked_label in self.marked_labels:
            marked_label.config(bg='white')

        self.marked_labels = []

    def mark_file_label(self, file_label, right_mouse_pressed=False):
        if right_mouse_pressed:
            if file_label in self.marked_labels:
                return
            else:
                self.unmark_all_file_labels()

        elif not self.is_ctrl_pressed:
            self.unmark_all_file_labels()

        file_label.config(bg='#b3d9ff')
        self.marked_labels.append(file_label)

    def remove_marked_files(self):
        for file_label in self.marked_labels:
            self.ui_operations.delete_file_from_current_path(file_label.file_name, file_label.is_dir)

        self.unmark_all_file_labels()

    def download_marked_files(self):
        non_dir_labels = filter(lambda l: not l.is_dir, self.marked_labels)
        if len(non_dir_labels) > 1:
            path = tkFileDialog.askdirectory(parent=self.parent, title='Select directory to save files')
            if path:
                for file_label in non_dir_labels:
                    self.ui_operations.download_from_current_server_path(file_label.file_name,
                                        file_path_on_client=os.path.join(path, file_label.file_name))
        elif len(non_dir_labels) == 1:
            path = tkFileDialog.asksaveasfilename(parent=self.parent, initialfile=non_dir_labels[0].file_name,
                                                  title='Select directory to save files')
            if path:
                self.ui_operations.download_from_current_server_path(non_dir_labels[0].file_name,
                                    file_path_on_client=path)

        self.unmark_all_file_labels()

    def control_pressed_or_released(self, state):
        """
        Change the state of the control key
        param state: True if mouse Pressed, False if mouse Released
        """
        self.is_ctrl_pressed = state

    def refresh_display(self, group=''):
        map(lambda x: x.destroy(), self.currently_on_screen)
        self.file_labels = []
        self.dir_labels = []
        self.marked_labels = []
        self._num_of_files = 0

        file_names, dir_names = self.ui_operations.list_files_in_current_dir()
        self._add_file_labels(file_names, dir_names)
        self.currently_on_screen = self.dir_labels + self.file_labels

    def __init__(self, parent, ui_operations):
        """
        :param: file_names: list of files to display.
        """
        tk.Canvas.__init__(self, parent, background='white', borderwidth=0, highlightthickness=0)
        self.files_frame = tk.Frame(self, background='white')
        self.parent = parent
        self.ui_operations = ui_operations
        self.path = ui_operations.current_server_path

        # Create vertical scrollbar
        self.files_scrollbar = tk.Scrollbar(self, orient="vertical", command=self.yview)
        self.configure(yscrollcommand=self.files_scrollbar.set)
        self.files_scrollbar.pack(side="right", fill="y")
        self.pack(side="top", fill="both", expand=True)
        self.create_window((0, 0), window=self.files_frame, anchor="nw")
        self.files_frame.bind("<Configure>", lambda event, canvas=self: self.onFrameConfigure())

        self.currently_on_screen = []
        self.refresh_display()

        self.marked_labels = []
        self.is_ctrl_pressed = False
        parent.bind("<KeyPress-Control_L>", lambda event: self.control_pressed_or_released(True))
        parent.bind("<KeyRelease-Control_L>", lambda event: self.control_pressed_or_released(False))

        self.bind("<Button-1>", lambda event: self.unmark_all_file_labels())

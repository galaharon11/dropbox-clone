import Tkinter as tk
import subprocess
import os
import traceback
from PIL import Image
import tkFileDialog
import tkMessageBox

from FileLabel import FileLabel


class FileDisplay(tk.Canvas):
    def _get_nubmer_of_coluns(self):
        self.update()
        return self.winfo_width() // 95

    def _add_file_labels(self, file_names, dir_names=[]):
        extensions = set()
        number_of_columns = self._get_nubmer_of_coluns()
        for dir_name_to_add in dir_names:
            dir_label = FileLabel(self.files_frame, self, dir_name_to_add, self._num_of_files,
                                  self.ui_operations, is_dir=True)
            dir_label.do_grid(self._num_of_files, number_of_columns)
            extensions.add('directory')
            self.dir_labels.append(dir_label)
            self._num_of_files += 1

        for file_name_to_add in file_names:
            file_label = FileLabel(self.files_frame, self, file_name_to_add, self._num_of_files, self.ui_operations)
            file_label.do_grid(self._num_of_files, number_of_columns)
            extensions.add(file_label.file_extension[1:])
            self.file_labels.append(file_label)
            self._num_of_files += 1

        icon_dir_path = os.path.join(os.path.dirname(__file__), 'icons')
        images = self.get_icon_for_extensions(icon_dir_path, list(extensions))

        for dir_label in self.dir_labels:
            dir_label.add_image(images['directory'])

        for file_label in self.file_labels:
            file_label.add_image(images[file_label.file_extension[1:]])

    def _chagne_size(self):
        for x in self.currently_on_screen:
            x.grid_forget()

        number_of_columns = self._get_nubmer_of_coluns()
        self._num_of_files = 0

        for file_label in self.currently_on_screen:
            file_label.do_grid(self._num_of_files, number_of_columns)
            self._num_of_files += 1

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

        number_of_columns = self._get_nubmer_of_coluns()
        self.currently_on_screen = []
        self._num_of_files = 0

        dir_labels = filter(lambda x: x.file_name in dir_names, self.dir_labels)
        file_labels = filter(lambda x: x.file_name in file_names, self.file_labels)
        for dir_name_to_add in dir_labels:
            dir_name_to_add.do_grid(self._num_of_files, number_of_columns)
            self.currently_on_screen.append(dir_name_to_add)
            self._num_of_files += 1
        for file_name_to_add in file_labels:
            file_name_to_add.do_grid(self._num_of_files, number_of_columns)
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


    def download_next_file_if_last_finished(self, path_on_client, names):
        if self.ui_operations.download_completed:
            file_name = names.pop()
            self.ui_operations.download_from_current_server_path(file_name,
                               os.path.join(path_on_client, file_name), show_message_box=False)
        if names:
            self.after_cancel(self.after_instance)
            self.after_instance = self.after(100, lambda:
                                  self.download_next_file_if_last_finished(path_on_client, names))

    def download_dir(self, path_on_client, dir_name):
        os.mkdir(os.path.join(path_on_client, dir_name))
        dirs, files = self.ui_operations.recursive_list(dir_name)
        for d in dirs:
            d = d[1:]
            os.makedirs(os.path.join(path_on_client, d))
        if files:
            # Remove file's prefix. /a/b/c -> a/b/c
            files = map(lambda f: f[1:], files)
            return files
        return []

    def download_marked_files(self):
        if len(self.marked_labels) > 1:
            path_to_dir = tkFileDialog.askdirectory(parent=self.parent, title='Select directory to save files')
            if path_to_dir:
                ignored_files = filter(lambda label: os.path.exists(os.path.join(
                                        path_to_dir ,label.file_name)), self.marked_labels)
                if ignored_files:
                    ignored_files_string = ', '.join(map(lambda label: label.file_name , ignored_files))
                    tkMessageBox.showwarning(title='Warning', message=u'This directory already contain a file(s) '
                    'with the name(s) {0}. The program will not download those file(s)'.format(ignored_files_string))

                labels = list(set(self.marked_labels) - set(ignored_files))

                files_to_download = []
                for l in labels:
                    name = l.file_name
                    if l.is_dir:
                        files_to_download += self.download_dir(path_to_dir, name)
                    else:
                        files_to_download.append(name)
                if files_to_download:
                    first_file = files_to_download.pop()
                    path_to_file = os.path.join(path_to_dir, first_file)
                    self.ui_operations.download_from_current_server_path(first_file,
                                        path_to_file, show_message_box=False)
                    # The donwlaod function is async but we need to download many files.
                    # after() can help with this problem.
                    self.after_instance = self.after(100, lambda:
                        self.download_next_file_if_last_finished(path_to_dir, files_to_download))

        elif len(self.marked_labels) == 1:
            path_to_dir = tkFileDialog.asksaveasfilename(parent=self.parent, initialfile=self.marked_labels[0].file_name,
                                                  title='Save file')
            if path_to_dir:
                name = self.marked_labels[0].file_name
                if self.marked_labels[0].is_dir:
                    path_to_dir = os.path.dirname(path_to_dir)
                    files_to_download = self.download_dir(path_to_dir, name)
                    if files_to_download:
                        first_file = files_to_download.pop()
                        path_to_file = os.path.join(path_to_dir, first_file)
                        self.ui_operations.download_from_current_server_path(first_file,
                                            path_to_file, show_message_box=False)
                        # The donwlaod function is async but we need to download many files.
                        # after() can help with this problem.
                        self.after_instance = self.after(100, lambda:
                            self.download_next_file_if_last_finished(path_to_dir, files_to_download))

                else:
                    self.ui_operations.download_from_current_server_path(name,
                                                path_to_dir, is_dir=self.marked_labels[0].is_dir)

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
        file_names: list of files to display.
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
        self.bind("<Configure>", lambda event: self._chagne_size())

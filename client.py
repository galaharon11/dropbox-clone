import Tkinter as tk
import tkFont
import os
import sys
import socket

from components.FileDisplay import FileDisplay
from components.ControlFrame import ControlFrame
from components.LoginWindow import LoginWindow
from components.RegisterWindow import RegisterWindow
from components.GroupsView import GroupsView
from UIOperations import UIOperations

is_ctrl_pressed = True
files_window = None
entry_on_focus = None
control_frame = None
login_server_addr = ("10.100.102.15", 10054)
ftp_control_addr = ("10.100.102.15", 21)


def close_program(files_window):
    files_window.destroy()
    tmp_folder_path = os.path.join(os.path.realpath('.'), 'tmp')
    try:
        for filename in os.listdir(tmp_folder_path):
            tmp_file_path = os.path.join(tmp_folder_path, filename)
            os.unlink(tmp_file_path)
    except:
        pass
    sys.exit()


def unfocus_entries(event):
    global entry_on_focus
    focused_widget = files_window.focus_get()
    if focused_widget.winfo_class() == "Entry":
        if entry_on_focus == focused_widget:
            files_window.focus_set()
            control_frame.set_search_text()
            entry_on_focus = None
        else:
            entry_on_focus = focused_widget
    else:
        entry_on_focus = None


def spawn_login_frame(is_register_window=False):
    global login_window
    if(is_register_window):
        login_window = RegisterWindow(welcome_window, login_sock, create_main_window)
    else:
        login_window = LoginWindow(welcome_window, login_sock, create_main_window)


def create_main_window(user_name):
    global files_window, control_frame

    session_id = login_sock.recv(1024)
    session_id = int(session_id[session_id.find('SESSIONID ') + 10:])
    login_sock.close()

    ftp_control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ftp_control_sock.connect(ftp_control_addr)

    files_window = tk.Toplevel(welcome_window)

    files_window.title('Dropbox')
    files_window.geometry('950x700+50+50')

    ui_operations = UIOperations(files_window, ftp_control_sock, '\\', session_id, ftp_control_addr[0], user_name)

    default_font = tkFont.nametofont("TkTextFont")
    default_font.configure(size=12)

    file_display = FileDisplay(files_window, ui_operations)
    file_display.grid(row=1, column=1, sticky='snwe', padx=(0,10), pady=(0, 20))

    control_frame = ControlFrame(files_window, file_display, ui_operations)
    control_frame.grid(row=0, column=0, columnspan=2, pady=(10, 0), padx=20, sticky='ew')
    ui_operations.update_compenents(file_display=file_display, control_frame=control_frame)

    groups_view = GroupsView(files_window, ui_operations)
    groups_view.grid(row=1, column=0,sticky='sn', pady=(0,20), padx=(10,0))

    files_window.grid_rowconfigure(1, weight=20)
    files_window.grid_rowconfigure(0, weight=1)
    files_window.grid_columnconfigure(0, weight=1)
    files_window.grid_columnconfigure(1, weight=20000)

    files_window.bind("<Button-1>", unfocus_entries)

    files_window.protocol("WM_DELETE_WINDOW", lambda: close_program(files_window))

    welcome_window.withdraw()
    login_window.withdraw()

    files_window.mainloop()


def main():
    global welcome_window, login_sock

    welcome_window = tk.Tk()
    welcome_window.geometry("+200+100")
    welcome_window.resizable(False, False)
    welcome_window.title('Welcome')

    login_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    login_sock.connect(login_server_addr)

    widgets_font = tkFont.Font(family="TkTextFont", size=20)
    login_button = tk.Button(welcome_window, text="Login", font=widgets_font,
                            command=lambda: spawn_login_frame(False))
    register_button = tk.Button(welcome_window, text="Create an acount", font=widgets_font,
                                command=lambda: spawn_login_frame(True))
    login_button.pack(pady=10, padx=10)
    register_button.pack(pady=10, padx=10)

    welcome_window.mainloop()


if __name__ == '__main__':
    # This line allows modules to import python files within the program
    sys.path.append(os.path.dirname(sys.path[0]))
    main()

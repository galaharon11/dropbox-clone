import Tkinter as tk
import tkFont
import tkMessageBox
import socket

class LoginWindow(tk.Toplevel):
    def close_window(self):
        self.destroy()

    def do_login(self, username, password):
        try:
            if len(username) < 4 or len(password) < 4:
                tkMessageBox.showerror('Error', 'Username and password should contain at least 4 characters')
                return
            if not (username.isalnum() and password.isalnum()):
                tkMessageBox.showerror('Error', 'Name and username should contain english letters and characters only')
                return

            login_str = ';'.join(['login', username, password])
            self.login_server_socket.send(login_str)
            error = self.login_server_socket.recv(1024)
            if error != 'success':
                tkMessageBox.showinfo('error', error)
                self.focus_force()
                self.username_entry.delete(0, 'end')
                self.password_entry.delete(0, 'end')

            else:
                self.do_func_when_exit(username)
                self.destroy()
        except UnicodeEncodeError:
            tkMessageBox.showerror('Error', 'Name and username should contain english letters and characters only')
        except socket.error:
            tkMessageBox.showerror('Server disconnected', 'The server was terminated. Please make sure the server is '
                                                            'running and try again')
            exit()

    def __init__(self, parent, login_server_socket, do_func_when_exit):
        tk.Toplevel.__init__(self, parent)
        self.resizable(False, False)
        self.geometry("+250+130")
        self.title('Login')
        self.parent = parent

        self.login_server_socket = login_server_socket
        self.do_func_when_exit = do_func_when_exit

        login_label_font = tkFont.Font(family="TkTextFont", size=26)
        self.login_label = tk.Label(self, text="Login", font=login_label_font)
        self.login_label.grid(column=0, row=0, pady=10, padx=10, columnspan=2)

        widgets_font = tkFont.Font(family="TkTextFont", size=18)

        self.username_label = tk.Label(self, text="Username:", font=widgets_font)
        self.username_entry = tk.Entry(self, font=widgets_font, width=30)
        self.username_entry.grid(column=1, row=1, pady=10, padx=10)
        self.username_label.grid(column=0, row=1, pady=10, padx=10)

        self.password_label = tk.Label(self, text="Password:", font=widgets_font)
        self.password_entry = tk.Entry(self, font=widgets_font, width=30, show='*')
        self.password_entry.grid(column=1, row=2, pady=10, padx=10)
        self.password_label.grid(column=0, row=2, pady=10, padx=10)

        self.login_button = tk.Button(self, text="Login", font=widgets_font, command=lambda:
                                      self.do_login(self.username_entry.get(), self.password_entry.get()))
        self.login_button.grid(column=0, row=3, columnspan=2, pady=10, padx=10)

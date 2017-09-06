#!/usr/bin/python
# -*- coding: utf-8 -*-

###########################################################################
# Ava's Global speedrunning leaderboard
# Copyright (C) 2017 Samuel Therrien
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact:
# samuel.06@hotmail.com
###########################################################################

import _thread
import os.path
from tkinter import *

from user_updater import *


def resource_path(relative_path):
    """ Get absolute path to resource, works for "--onefile" in PyInstaller. """
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


with open(resource_path("LICENSE.txt"), "r") as f: LICENSE = f.read()
with open(resource_path("README.md"), "r") as f: README = f.read()
window = Tk()
window.iconbitmap(resource_path("favicon.ico"))
window.title("Global speedrunning leaderboard")
window.geometry("664x264")
# window.minsize(foo, bar)
defaultCode = "Avasam"


def write_text(s):
    text.configure(state=NORMAL)
    text.delete('1.0', END)
    text.insert(INSERT, str(s))
    text.configure(state=DISABLED)


def show_help():
    write_text(README)


def update_user():
    update_userButton.configure(state=DISABLED)
    _thread.start_new_thread(update_user_thread, (entry.get(), statusLabel))


def update_user_thread(p_code, p_statusLabel):
    try:
        result = get_updated_user(p_code, p_statusLabel)
        write_text(result)
    except UserUpdaterError as exception:
        print("\n{}\n{}".format(exception.args[0]["error"], exception.args[0]["details"]))
        statusLabel.configure(text=("Error: {}".format(exception.args[0]["error"])))
        write_text(exception.args[0]["details"])
    except Exception:
        print("\nError: Unknown\n{}".format(traceback.format_exc()))
        statusLabel.configure(text=("Error: Unknown"))
        write_text(traceback.format_exc())
    update_userButton.configure(state=NORMAL)


def copy():
    window.clipboard_clear()
    window.clipboard_append(text.get('1.0', END))


def copyleft():
    write_text(LICENSE)


# Main Frame to create border spacing
mainFrame = Frame(window, bg="darkred")
mainFrame.pack(expand=YES, fill=BOTH, padx=4, pady=(0, 4))

# Top Frames
topFrame = Frame(mainFrame, bg="darkred")
topFrame.pack(side=TOP, fill=X, padx=4, pady=4)
# Entry Frame
entryFrame = Frame(topFrame)
entryFrame.pack(side=LEFT, expand=1, fill=X)
# Code Entry
label = Label(entryFrame, text="Enter a runner's name or id_: ")
label.pack(side=LEFT)
v = StringVar()
v.set(defaultCode)
entry = Entry(entryFrame, textvariable=v)
entry.pack(side=LEFT, expand=YES, fill=X)
# Help Button
button = Button(topFrame, text="?", command=show_help)
button.pack(side=RIGHT, padx=2)

# Middle Frame
textFrame = Frame(mainFrame, bg="darkred")
textFrame.pack(side=TOP, expand=1, fill=BOTH, padx=4)
textFrame.pack_propagate(False)
# Execution status
statusLabel = Label(textFrame)
statusLabel.pack(fill=X)
# Text Scrollbar
scrollbar = Scrollbar(textFrame)
scrollbar.pack(side=RIGHT, fill=Y)
# Text area
text = Text(textFrame, state=DISABLED, yscrollcommand=scrollbar.set)
text.pack(expand=YES, fill=BOTH)
scrollbar.config(command=text.yview)

# Bottom Frame
buttonsFrame = Frame(mainFrame, bg="darkred")
buttonsFrame.pack(fill=X, padx=4, pady=4)

# !Autoupdater
# auto_update_users_thread = AutoUpdateUsers(statusLabel, name="Auto Update Users Thread")
# auto_update_users_thread.start()
# def pause_unpause_auto_update():
#    if auto_update_users_thread.paused:
#        auto_update_users_thread.paused = False
#        auto_update_users_button.configure(text = "Pause auto-updating users")
#    else:
#        statusLabel.configure(text="Paused the automatic updating.")
#        auto_update_users_thread.paused = True
#        auto_update_users_button.configure(text = "Start auto-updating users")
# auto_update_users_button = Button(buttonsFrame, text="Start auto-updating users", command=pause_unpause_auto_update)
# auto_update_users_button.pack(side=LEFT, padx=(0,8))

# Update User Button
update_userButton = Button(buttonsFrame, text="Update runner", command=update_user)
update_userButton.pack(side=LEFT, padx=(0, 4))
# Clipboard Button
button = Button(buttonsFrame, text="Copy to clipboard", command=copy)
button.pack(side=LEFT, padx=4)
# Copyleft button
button = Button(buttonsFrame, text="© 2016 Samuel Therrien", command=copyleft)
button.pack(side=RIGHT, padx=(4, 0))

mainloop()

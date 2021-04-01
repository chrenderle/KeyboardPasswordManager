#!/usr/bin/python3
from pykeepass import PyKeePass, create_database
from pykeepass.exceptions import CredentialsError
import glob
from pathlib import Path
from GUI import Gui, TextFieldElement, ButtonElement, TextBoxElement, Element
from Keyboard import LogicalKeyboard
import ST7789 as ST7789
import sys
import termios
import tty
import os
import threading
import time
import queue
import signal


class ApplicationState:
    database: PyKeePass = None
    database_name: str = ""
    entry = None
    attribute = None
    lock = threading.Lock()
    save = False
    stop_signal = False

    def __del__(self):
        del self.entry
        del self.database
        self.database_name = ""
        self.attribute = ""





# page attribute_edit
def attribute_edit():
    global application_state
    gui.clear()
    gui.add(TextFieldElement(application_state.attribute))
    custom_attribute = application_state.entry.get_custom_property(application_state.attribute)
    if application_state.attribute == "password":
        gui.add(TextBoxElement(application_state.entry.password))
    elif application_state.attribute == "username":
        gui.add(TextBoxElement(application_state.entry.username))
    elif application_state.attribute == "title":
        gui.add(TextBoxElement(application_state.entry.title))
    elif custom_attribute is not None:
        gui.add(TextBoxElement(custom_attribute))
    else:
        raise RuntimeError("Attribute doesnt exist")
    gui.add(ButtonElement("Save", onclickcallback=attribute_edit_save_button))
    gui.add(ButtonElement("Abort", onclickcallback=attribute_edit_abort_button))
    gui.show()


def attribute_edit_save_button(button: ButtonElement):
    global application_state
    value = gui.elements[1].value
    # set loading depending on if waiting for the lock
    gui.set_loading(application_state.lock.locked())
    application_state.lock.acquire()
    if application_state.attribute == "password":
        application_state.entry.password = value
    elif application_state.attribute == "username":
        application_state.entry.username = value
    elif application_state.attribute == "title":
        application_state.entry.title = value
    elif application_state.entry.get_custom_property(application_state.attribute) is not None:
        application_state.entry.set_custom_property(application_state.attribute, value)
    else:
        raise RuntimeError("Attribute doesnt exist")
    application_state.lock.release()
    application_state.save = True
    entry_overview()


def attribute_edit_abort_button(button: ButtonElement):
    global application_state
    application_state.attribute = None
    entry_overview()


# page attribute_show
def attribute_show():
    global application_state
    gui.clear()
    gui.add(TextFieldElement(application_state.attribute))
    custom_attribute = application_state.entry.get_custom_property(application_state.attribute)
    if application_state.attribute == "password":
        gui.add(TextBoxElement(application_state.entry.password, readonly=True))
    elif application_state.attribute == "username":
        gui.add(TextBoxElement(application_state.entry.username, readonly=True))
    elif application_state.attribute == "title":
        gui.add(TextBoxElement(application_state.entry.title, readonly=True))
    elif custom_attribute is not None:
        gui.add(TextBoxElement(custom_attribute, readonly=True))
    else:
        raise Exception("Attribute doesnt exist")
    gui.add(ButtonElement("Back", attribute_show_back_button))
    gui.show()


def attribute_show_back_button(button: ButtonElement):
    attribute_overview()


# page attribute_overview
def attribute_overview():
    global application_state
    gui.clear()
    gui.add(ButtonElement("Back", attribute_overview_back_button))
    gui.add(ButtonElement("Enter", attribute_overview_enter_button))
    gui.add(ButtonElement("Show", attribute_overview_show_button))
    gui.add(ButtonElement("Edit", attribute_overview_edit_button))
    # show delete button only for custom attributes
    if application_state.attribute not in ["title", "username", "password"]:
        gui.add(ButtonElement("Delete", attribute_overview_delete_button))
    gui.show()


def attribute_overview_back_button(button: ButtonElement):
    entry_overview()


def attribute_overview_enter_button(button: ButtonElement):
    global application_state
    value: str
    if application_state.attribute == "title":
        value = application_state.entry.title
    elif application_state.attribute == "username":
        value = application_state.entry.username
    elif application_state.attribute == "password":
        value = application_state.entry.password
    else:
        value = application_state.entry.get_custom_property(application_state.attribute)
    if keyboard.send_usb_string(value):
        attribute_overview()
    else:
        attribute_overview()
        gui.show_popup("enter failed")


def attribute_overview_show_button(button: ButtonElement):
    attribute_show()


def attribute_overview_edit_button(button: ButtonElement):
    attribute_edit()


def attribute_overview_delete_button(button: ButtonElement):
    global application_state
    application_state.entry.delete_custom_property(application_state.attribute)
    application_state.save = True
    entry_overview()


# page attribute_add
def attribute_add():
    gui.clear()
    gui.add(TextBoxElement("Emtpy attribute"))
    gui.add(TextBoxElement(""))
    gui.add(ButtonElement("Save", onclickcallback=attribute_add_save_button))
    gui.add(ButtonElement("Abort", onclickcallback=attribute_add_back_button))
    gui.show()


def attribute_add_save_button(button: ButtonElement):
    global application_state
    # set the custom attribute
    print("2: " + gui.elements[0].value)
    print("3: " + gui.elements[1].value)
    application_state.lock.acquire()
    application_state.entry.set_custom_property(gui.elements[0].value, gui.elements[1].value)
    application_state.lock.release()
    application_state.save = True
    # show the entry overview again
    entry_overview()


def attribute_add_back_button(button: ButtonElement):
    entry_overview()


# page entry_overview
def entry_overview():
    global application_state
    gui.clear()
    gui.add(TextFieldElement(application_state.entry.title))
    gui.add(ButtonElement("Back", onclickcallback=entry_overview_back_button))
    # show the standard attributes
    gui.add(ButtonElement("title", onclickcallback=entry_overview_show_attribute_button, argument="title"))
    gui.add(ButtonElement("username", onclickcallback=entry_overview_show_attribute_button, argument="username"))
    gui.add(ButtonElement("password", onclickcallback=entry_overview_show_attribute_button, argument="password"))
    print("1: " + str(len(application_state.entry.custom_properties)))
    for custom_attribute in application_state.entry.custom_properties:
        gui.add(ButtonElement(custom_attribute, onclickcallback=entry_overview_show_attribute_button,
                              argument=custom_attribute))
    gui.add(ButtonElement("Add attribute", onclickcallback=entry_overview_add_attribute_button))
    gui.add(ButtonElement("Delete", onclickcallback=entry_overview_delete_button))
    gui.show()


def entry_overview_back_button(button: ButtonElement):
    entry_list()


def entry_overview_show_attribute_button(button: ButtonElement):
    global application_state
    application_state.attribute = button.argument
    attribute_overview()


def entry_overview_add_attribute_button(button: ButtonElement):
    attribute_add()


def entry_overview_delete_button(button: ButtonElement):
    global application_state
    # show "loading"
    gui.set_loading(True)
    application_state.lock.acquire()
    print("deleting entry")
    print(application_state.entry)
    application_state.database.delete_entry(application_state.entry)
    print("deleting entry finished")
    application_state.lock.release()
    application_state.save = True
    application_state.entry = None
    entry_list()


# page database_list
def entry_list():
    global application_state
    gui.clear()
    gui.add(ButtonElement("Back", onclickcallback=entry_list_back_button))
    gui.add(ButtonElement("Add entry", onclickcallback=entry_list_add_entry_button))
    for entry in application_state.database.entries:
        gui.add(ButtonElement(entry.title, onclickcallback=entry_list_show_entry_button, argument=entry))
    gui.show()


def entry_list_show_entry_button(button: ButtonElement):
    global application_state
    application_state.entry = button.argument
    entry_overview()


def entry_list_back_button(button: ButtonElement):
    database_overview()


def entry_list_add_entry_button(button: ButtonElement):
    global application_state
    gui.set_loading(True)
    application_state.lock.acquire()
    application_state.entry = application_state.database.add_entry(application_state.database.root_group, "Empty entry",
                                                                   "", "")
    application_state.lock.release()
    application_state.save = True
    entry_overview()


# page database_settings
def database_settings():
    gui.clear()
    gui.add(ButtonElement("Back", database_settings_back_button))
    gui.add(ButtonElement("Change password", database_settings_change_password_button))
    gui.add(ButtonElement("Delete database", database_settings_delete_button))
    gui.show()


def database_settings_back_button(button: ButtonElement):
    database_overview()


def database_settings_change_password_button(button: ButtonElement):
    database_change_password()


def database_settings_delete_button(button: ButtonElement):
    global application_state
    gui.set_loading(True)
    application_state.lock.acquire()
    application_state.save = False
    # get the filename of the database
    filename = application_state.database.filename
    # delete the local data of the database
    del application_state
    application_state = ApplicationState()
    # delete the file
    os.remove(filename)
    # show the database list page again
    database_list()


# page database_change_password
def database_change_password():
    gui.clear()
    gui.add(ButtonElement("Back", onclickcallback=database_change_password_abort_button))
    gui.add(TextBoxElement("", placeholder="new password", obfuscated=True))
    gui.add(TextBoxElement("", placeholder="repeat", obfuscated=True))
    gui.add(ButtonElement("Save", onclickcallback=database_change_password_save_button))
    gui.show()


def database_change_password_abort_button(button: ButtonElement):
    database_settings()


def database_change_password_save_button(button: ButtonElement):
    global application_state
    # check if password match
    if gui.elements[1].value != gui.elements[2].value:
        # passwords do not match
        gui.show_popup("passwords do not match", popup_close_event=database_change_password_popup_event)
        return

    # change password
    # show "loading" when waiting for the lock
    gui.set_loading(application_state.lock.locked())
    application_state.lock.acquire()
    application_state.database.password = gui.elements[1].value
    application_state.lock.release()
    application_state.save = True
    database_settings()


def database_change_password_popup_event():
    gui.elements[1].value = ""
    gui.elements[2].value = ""
    gui.show()


# page database_create
def database_create():
    gui.clear()
    gui.add(ButtonElement("Abort", database_create_abort_button))
    gui.add(TextBoxElement("", placeholder="name"))
    gui.add(TextBoxElement("", placeholder="password", obfuscated=True))
    gui.add(TextBoxElement("", placeholder="repeat", obfuscated=True))
    gui.add(ButtonElement("Create", onclickcallback=database_create_create_button))
    gui.show()


def database_create_abort_button(button: ButtonElement):
    database_list()


def database_create_create_button(button: ButtonElement):
    global application_state
    # compare passwords
    if gui.elements[2].value != gui.elements[3].value:
        # passwords do not match
        # delete the password text box values
        gui.show_popup("passwords do not match", popup_close_event=database_create_popup_event)
        return
    # check if database name is not empty
    if gui.elements[1].value == "":
        # database name is empty
        # do nothing
        gui.show_popup("title can not be empty")
        return
    # create database
    gui.set_loading(True)
    application_state.lock.acquire()
    application_state.database_name = gui.elements[1].value
    application_state.database = create_database("/home/pi/.keepass/" + application_state.database_name + ".kdbx",
                                                 password=gui.elements[2].value)
    application_state.lock.release()
    application_state.save = True
    database_overview()


def database_create_popup_event():
    gui.elements[2].value = ""
    gui.elements[3].value = ""
    gui.show()


# page database_overview
def database_overview():
    gui.clear()
    gui.add(ButtonElement("Lock", onclickcallback=database_overview_close_button))
    gui.add(ButtonElement("Show entries", onclickcallback=database_overview_show_entries_button))
    gui.add(ButtonElement("Settings", onclickcallback=database_overview_settings_button))
    gui.show()


def database_overview_close_button(button: ButtonElement):
    global application_state
    gui.set_loading(True)
    application_state.save = False
    if application_state.lock.locked() is False:
        application_state.database.save()
    application_state.lock.acquire()
    application_state.database = None
    application_state.lock.release()
    database_list()


def database_overview_show_entries_button(button: ButtonElement):
    entry_list()


def database_overview_settings_button(button: ButtonElement):
    database_settings()


# page database_unlock
def database_unlock():
    # show the dialog for entering the password
    gui.clear()
    gui.add(TextFieldElement("Enter password"))
    gui.add(TextBoxElement("", placeholder="Password", obfuscated=True, onentercallback=database_unlock_button))
    gui.add(ButtonElement("Unlock", onclickcallback=database_unlock_button))
    gui.show()


def database_unlock_button(element: Element):
    global application_state
    global gui
    password = gui.elements[1].value
    try:
        gui.set_loading(True)
        application_state.database = PyKeePass("/home/pi/.keepass/" + application_state.database_name + ".kdbx",
                                               password=password)
    except CredentialsError:
        gui.show_popup("wrong credentials", popup_close_event=database_unlock_wrong_credentials_popup)
        return

    # display the entries in the database
    database_overview()


def database_unlock_back_button(button: ButtonElement):
    database_list()


def database_unlock_wrong_credentials_popup():
    database_unlock()


# page entry_list
def database_list():
    # get all databases in the password manager directory
    databases = glob.glob("/home/pi/.keepass/*.kdbx")

    gui.clear()
    for database in databases:
        gui.add(ButtonElement(database.replace("/home/pi/.keepass/", "").replace(".kdbx", ""),
                              onclickcallback=database_list_entry_button))
    gui.add(ButtonElement("Create Database", onclickcallback=database_list_create_button))
    gui.add(ButtonElement("Exit", onclickcallback=database_list_exit_button))
    gui.show()


# database_list button when selected an entry
def database_list_entry_button(button: ButtonElement):
    global application_state
    application_state.database_name = button.value
    database_unlock()


# database_list button when creating a new database
def database_list_create_button(button: ButtonElement):
    database_create()


def database_list_exit_button(button: ButtonElement):
    exit_program()


def exit_program():
    global keyboard
    global application_state
    print("deleting logical keyboard")
    keyboard.cleanup()
    print("set stop signal for thread")
    application_state.stop_signal = True
    print("waiting for thread to end")
    while save_thread.is_alive() is True:
        pass
    print("thread ended")
    exit()


def getch() -> str:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def save_thread_function():
    global application_state
    while application_state.stop_signal is False:
        if application_state.save is True:
            application_state.lock.acquire()
            print("saving")
            application_state.database.save()
            print("saved")
            application_state.save = False
            application_state.lock.release()
        time.sleep(1)


def get_keyboard_input():
    global q
    while True:
        gui.text_input(q.get(block=True))


def signal_handler(sig, frame):
    exit_program()


if __name__ == "__main__":

    # create gui
    display = ST7789.ST7789(port=0,
                            cs=ST7789.BG_SPI_CS_FRONT,
                            dc=25,
                            rst=24,
                            backlight=27,
                            spi_speed_hz=80 * 1000 * 1000,
                            mode=3)

    gui = Gui(display)

    # create the folder with the databases if it not exists
    Path("/home/pi/.keepass").mkdir(parents=True, exist_ok=True)
    application_state = ApplicationState()
    q = queue.Queue()
    keyboard = LogicalKeyboard(q)
    save_thread = threading.Thread(target=save_thread_function)
    save_thread.start()
    database_list()
    q.put("PASSWORD_MANAGER_ENABLE")
    signal.signal(signal.SIGINT, signal_handler)
    try:
        print("ready")
        get_keyboard_input()
    except KeyboardInterrupt:
        exit_program()

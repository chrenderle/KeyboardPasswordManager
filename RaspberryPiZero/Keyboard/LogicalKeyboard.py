from .PhysicalKeyboard import PhysicalKeyboard
from .USBKeyboard import USBKeyboard
from .Config import get_config, get_qwertz_layer_1, get_qwertz_layer_2, get_qwertz_layer_3
import queue
import threading


class LogicalKeyboard:
    __physical_keyboard: PhysicalKeyboard = None
    __usb_keyboard: USBKeyboard = None
    __mode: bool = False
    __config: dict = get_config()
    __qwertz_layer_1: dict = get_qwertz_layer_1()
    __qwertz_layer_2: dict = get_qwertz_layer_2()
    __qwertz_layer_3: dict = get_qwertz_layer_3()
    __q: queue.Queue
    __lshift_status: bool = False
    __rshift_status: bool = False
    __altgr_status: bool = False
    __caps_lock_status: bool = False
    __lock: threading.Lock = threading.Lock()

    def __init__(self, q: queue.Queue):
        self.__physical_keyboard = PhysicalKeyboard(self.__on_click_callback, self.__on_release_callback)
        self.__usb_keyboard = USBKeyboard()
        self.__q = q

    def __on_click_callback(self, key: int):
        self.__lock.acquire()
        key_str = self.__config.get(key)
        if key_str is None:
            raise RuntimeError("Key int not found")
        elif key_str is "LSHIFT":
            self.__lshift_status = True
        elif key_str is "RSHIFT":
            self.__rshift_status = True
        elif key_str is "CAPS":
            self.__caps_lock_status = not self.__caps_lock_status
        elif key_str is "ALTGR":
            self.__altgr_status = True
        elif key_str is "PASSWORD_MANAGER_ENABLE":
            self.__mode = not self.__mode
            self.__q.put("PASSWORD_MANAGER_ENABLE")

        if self.__mode:
            # altgr ignores shift
            if self.__altgr_status is True:
                key_str_value = self.__qwertz_layer_3.get(key_str)
            # handle if caps lock is pressed
            elif self.__caps_lock_status is True:
                # caps lock and shift equalize each other
                if self.__lshift_status or self.__rshift_status:
                    key_str_value = self.__qwertz_layer_1.get(key_str)
                else:
                    key_str_value = self.__qwertz_layer_2.get(key_str)
            # only shift pressed
            elif self.__lshift_status or self.__rshift_status:
                key_str_value = self.__qwertz_layer_2.get(key_str)
            # normal input
            else:
                key_str_value = self.__qwertz_layer_1.get(key_str)
            # if no string was returned we dont want to pass anything to the password manager
            if key_str_value is None:
                self.__lock.release()
                return
            self.__q.put(key_str_value)
        else:
            self.__usb_keyboard.press_key(key_str)
        self.__lock.release()

    def __on_release_callback(self, key: int):
        self.__lock.acquire()
        key_str = self.__config[key]
        if key_str is None:
            raise RuntimeError("key int not found")
        elif key_str is "LSHIFT":
            self.__lshift_status = False
        elif key_str is "RSHIFT":
            self.__rshift_status = False
        elif key_str is "ALTGR":
            self.__altgr_status = False
        # the releasing of keys doesnt matter for the password manager so only pass the release to the usb keyboard
        if not self.__mode:
            self.__usb_keyboard.release_key(key_str)
        self.__lock.release()

    def send_usb_string(self, string: str) -> bool:
        return self.__usb_keyboard.send_string(string)

    def cleanup(self):
        self.__physical_keyboard.cleanup()

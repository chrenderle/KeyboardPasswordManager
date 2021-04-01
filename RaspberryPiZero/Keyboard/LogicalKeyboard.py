from .PhysicalKeyboard import PhysicalKeyboard
from .USBKeyboard import USBKeyboard
from .Config import get_config, get_qwertz_layer_1, get_qwertz_layer_2, get_qwertz_layer_3
import queue
import threading


class LogicalKeyboard:
    physical_keyboard: PhysicalKeyboard = None
    usb_keyboard: USBKeyboard = None
    mode: bool = False
    config: dict = get_config()
    qwertz_layer_1: dict = get_qwertz_layer_1()
    qwertz_layer_2: dict = get_qwertz_layer_2()
    qwertz_layer_3: dict = get_qwertz_layer_3()
    q: queue.Queue
    lshift_status = False
    rshift_status = False
    altgr_status = False
    caps_lock_status = False
    lock: threading.Lock = threading.Lock()

    def __init__(self, q: queue.Queue):
        self.physical_keyboard = PhysicalKeyboard(self.__on_click_callback, self.__on_release_callback)
        self.usb_keyboard = USBKeyboard()
        self.q = q

    def __on_click_callback(self, key: int):
        self.lock.acquire()
        key_str = self.config.get(key)
        if key_str is None:
            raise RuntimeError("Key int not found")
        elif key_str is "LSHIFT":
            self.lshift_status = True
        elif key_str is "RSHIFT":
            self.rshift_status = True
        elif key_str is "CAPS":
            self.caps_lock_status = not self.caps_lock_status
        elif key_str is "ALTGR":
            self.altgr_status = True
        elif key_str is "PASSWORD_MANAGER_ENABLE":
            self.mode = not self.mode
            self.q.put("PASSWORD_MANAGER_ENABLE")

        if self.mode:
            # altgr ignores shift
            if self.altgr_status is True:
                key_str_value = get_qwertz_layer_3().get(key_str)
            # handle if caps lock is pressed
            elif self.caps_lock_status is True:
                # caps lock and shift equalize each other
                if self.lshift_status or self.rshift_status:
                    key_str_value = get_qwertz_layer_1().get(key_str)
                else:
                    key_str_value = get_qwertz_layer_2().get(key_str)
            # only shift pressed
            elif self.lshift_status or self.rshift_status:
                key_str_value = get_qwertz_layer_2().get(key_str)
            # normal input
            else:
                key_str_value = get_qwertz_layer_1().get(key_str)
            # if no string was returned we dont want to pass anything to the password manager
            if key_str_value is None:
                self.lock.release()
                return
            self.q.put(key_str_value)
        else:
            self.usb_keyboard.press_key(key_str)
        self.lock.release()

    def __on_release_callback(self, key: int):
        self.lock.acquire()
        key_str = self.config[key]
        if key_str is None:
            raise RuntimeError("key int not found")
        elif key_str is "LSHIFT":
            self.lshift_status = False
        elif key_str is "RSHIFT":
            self.rshift_status = False
        elif key_str is "ALTGR":
            self.altgr_status = False
        # the releasing of keys doesnt matter for the password manager so only pass the release to the usb keyboard
        if not self.mode:
            self.usb_keyboard.release_key(key_str)
        self.lock.release()

    def send_usb_string(self, string: str) -> bool:
        return self.usb_keyboard.send_string(string)

    def cleanup(self):
        self.physical_keyboard.cleanup()

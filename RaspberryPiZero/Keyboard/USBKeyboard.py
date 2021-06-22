from .Config import get_modifier_usb_keycodes, get_usb_keycodes, get_keycodes_from_char


class USBKeyboard:
    __pressed_keys = []
    __pressed_modifier_keys = []
    __modifier_config: dict
    __config: dict
    __char_config: dict

    def __init__(self):
        self.__modifier_config = get_modifier_usb_keycodes()
        self.__config = get_usb_keycodes()
        self.__char_config = get_keycodes_from_char()

    def press_key(self, key: str):
        self.__press_key_without_sending(key)
        self.__send_data()

    def __press_key_without_sending(self, key: str):
        print("usb press: " + key)
        keycode = self.__config.get(key)
        keycode_modifier = self.__modifier_config.get(key)
        if keycode is None and keycode_modifier is None:
            return
        if keycode is not None and keycode not in self.__pressed_keys and len(self.__pressed_keys) <= 6:
            self.__pressed_keys.append(keycode)
        elif keycode_modifier is not None and keycode_modifier not in self.__pressed_modifier_keys:
            self.__pressed_modifier_keys.append(keycode_modifier)

    def release_key(self, key: str):
        self.__release_key_without_sending(key)
        self.__send_data()

    def __release_key_without_sending(self, key: str):
        keycode = self.__config.get(key)
        keycode_modifier = self.__modifier_config.get(key)
        if keycode is None and keycode_modifier is None:
            return
        if keycode in self.__pressed_keys:
            self.__pressed_keys.remove(keycode)
        elif keycode_modifier in self.__pressed_modifier_keys:
            self.__pressed_modifier_keys.remove(keycode_modifier)

    def send_string(self, string: str) -> bool:
        self.__pressed_keys = []
        self.__pressed_modifier_keys = []
        for char in string:
            keycodes = self.__char_config.get(char)
            if char is None:
                return False
            for keycode in keycodes:
                self.__press_key_without_sending(keycode)
            self.__send_data()
            for keycode in keycodes:
                self.__release_key_without_sending(keycode)
            self.__send_data()
        return True

    def __send_data(self):
        data = bytearray([0, 0, 0, 0, 0, 0, 0, 0])
        for modifier in self.__pressed_modifier_keys:
            data[0] += modifier
        for i in range(len(self.__pressed_keys)):
            data[2 + i] = self.__pressed_keys[i]
        with open("/dev/hidg0", "rb+") as fd:
            fd.write(data)

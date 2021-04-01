from .Config import get_modifier_usb_keycodes, get_usb_keycodes, get_keycodes_from_char


class USBKeyboard:
    pressed_keys = []
    pressed_modifier_keys = []
    modifier_config: dict
    config: dict
    char_config: dict

    def __init__(self):
        self.modifier_config = get_modifier_usb_keycodes()
        self.config = get_usb_keycodes()
        self.char_config = get_keycodes_from_char()

    def press_key(self, key: str):
        self.__press_key_without_sending(key)
        self.__send_data()

    def __press_key_without_sending(self, key: str):
        print("usb press: " + key)
        keycode = self.config.get(key)
        keycode_modifier = self.modifier_config.get(key)
        if keycode is None and keycode_modifier is None:
            return
        if keycode is not None and keycode not in self.pressed_keys and len(self.pressed_keys) <= 6:
            self.pressed_keys.append(keycode)
        elif keycode_modifier is not None and keycode_modifier not in self.pressed_modifier_keys:
            self.pressed_modifier_keys.append(keycode_modifier)

    def release_key(self, key: str):
        self.__release_key_without_sending(key)
        self.__send_data()

    def __release_key_without_sending(self, key: str):
        keycode = self.config.get(key)
        keycode_modifier = self.modifier_config.get(key)
        if keycode is None and keycode_modifier is None:
            return
        if keycode in self.pressed_keys:
            self.pressed_keys.remove(keycode)
        elif keycode_modifier in self.pressed_modifier_keys:
            self.pressed_modifier_keys.remove(keycode_modifier)

    def send_string(self, string: str) -> bool:
        self.pressed_keys = []
        self.pressed_modifier_keys = []
        for char in string:
            keycodes = self.char_config.get(char)
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
        for modifier in self.pressed_modifier_keys:
            data[0] += modifier
        for i in range(len(self.pressed_keys)):
            data[2 + i] = self.pressed_keys[i]
        with open("/dev/hidg0", "rb+") as fd:
            fd.write(data)

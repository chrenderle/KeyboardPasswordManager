import RPi.GPIO as GPIO
import threading
import time
import smbus2
import _thread

COL_0 = 23
COL_1 = 8
COL_2 = 7
COL_3 = 12
COL_4 = 16
COL_5 = 20
COL_6 = 21
COL = [COL_0, COL_1, COL_2, COL_3, COL_4, COL_5, COL_6]

ROW_0 = 5
ROW_1 = 6
ROW_2 = 13
ROW_3 = 19
ROW_4 = 26
ROW = [ROW_0, ROW_1, ROW_2, ROW_3, ROW_4]


class PhysicalKeyboard:
    on_key_press: callable = None
    on_key_release: callable = None
    __key_states = [False] * (len(ROW) * len(COL))
    __key_timestamp = []
    __some_button_pressed: bool = False
    __lock = None
    __bus = None

    def __init__(self, on_key_press: callable, on_key_release: callable):
        self.on_key_press = on_key_press
        self.on_key_release = on_key_release
        self.__init_gpio()
        self.__init_i2c()
        self.__lock = threading.Lock()

    def __init_gpio(self):
        GPIO.setmode(GPIO.BCM)
        for c in COL:
            GPIO.setup(c, GPIO.OUT)
            GPIO.output(c, GPIO.HIGH)
        for r in ROW:
            GPIO.setup(r, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            _thread.start_new_thread(self.__button_polling, ())

    def __init_i2c(self):
        self.__bus = smbus2.SMBus(1)
        time.sleep(1)
        _thread.start_new_thread(self.__poll_i2c, ())

    def __poll_i2c(self):
        while True:
            time.sleep(0.01)
            try:
                b = self.__bus.read_byte_data(8, 1)
            except OSError:
                continue
            key = b - 2
            if b == 1:
                continue
            elif 2 <= b < 37:
                self.__lock.acquire()
                self.on_key_press(key + 35)
                self.__lock.release()
            elif b >= 37:
                key = key - 35
                self.__lock.acquire()
                self.on_key_release(key + 35)
                self.__lock.release()

    # polls the gpios as long as one key is pressed
    def __button_polling(self):
        while True:
            for c in COL:
                GPIO.output(c, GPIO.LOW)
            for c in COL:
                GPIO.output(c, GPIO.HIGH)
                for r in ROW:
                    row_index = ROW.index(r)
                    col_index = COL.index(c)
                    key_id = row_index * 7 + col_index
                    if GPIO.input(r) == GPIO.HIGH and self.__key_states[key_id] is False:
                        self.__key_states[key_id] = True
                        self.__lock.acquire()
                        self.on_key_press(key_id)
                        self.__lock.release()
                    elif GPIO.input(r) == GPIO.LOW and self.__key_states[key_id] is True:
                        self.__key_states[key_id] = False
                        self.__lock.acquire()
                        self.on_key_release(key_id)
                        self.__lock.release()
                GPIO.output(c, GPIO.LOW)
            time.sleep(0.01)

    def __check_some_button_pressed(self):
        state = False
        for key in self.__key_states:
            if key is True:
                state = True
                break
        self.__some_button_pressed = state

    def cleanup(self):
        GPIO.cleanup()

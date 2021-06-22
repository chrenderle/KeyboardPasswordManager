# Modul für die Gui
import ST7789 as ST7789
from PIL import Image, ImageDraw, ImageFont
from .Element import Element
from .ButtonElement import ButtonElement
from .TextBoxElement import TextBoxElement
from .TextFieldElement import TextFieldElement


class Gui:
    position = -1
    display = None
    image = None
    elements = []
    popup = False
    popup_close_event: callable = None

    def __init__(self, display: ST7789):
        self.display = display
        self.display.begin()
        return

    def add(self, element: Element):
        if len(self.elements) == 0:
            self.position = 0
        self.elements.append(element)
        return

    def clear(self):
        self.elements = []
        self.position = -1
        return

    def delete(self, index: int) -> Element:
        if len(self.elements) == 1:
            self.position = -1
        return self.elements.pop(index)

    def update(self, element: Element, index: int):
        self.elements[index] = element
        return

    def scroll_vertical(self, diff: int):
        # if the selected element is of type text box scroll
        if isinstance(self.elements[self.position], TextBoxElement):
            self.elements[self.position].scroll(diff)
        self.__update_display()

    def scroll(self, diff: int):
        if self.position + diff < 0 or self.position + diff >= len(self.elements):
            # scroll makes no effect
            return
        self.position += diff
        self.__update_display()
        return

    def set_position(self, position: int):
        if position < 0 or position >= len(self.elements):
            raise RuntimeError("position out of bound")
        self.position = position
        self.__update_display()
        return

    def set_loading(self, value: bool):
        if value is False:
            return
        draw = ImageDraw.Draw(self.image)
        (WIDTH, HEIGHT) = (240, 240)
        (width, height) = (100, 40)
        (x1, y1) = ((WIDTH - width) / 2, (HEIGHT - height) / 2)
        draw.rectangle(((x1, y1), (WIDTH - x1, HEIGHT - y1)), width=1, fill="blue")
        font = ImageFont.truetype("arial.ttf", 30)
        draw.text((x1, y1), "loading", font=font)
        self.display.display(self.image)

    def show_popup(self, text: str, fill: str = "red", popup_close_event: callable = None):
        draw = ImageDraw.Draw(self.image)
        (WIDTH, HEIGHT) = (240, 240)
        (width, height) = (200, 150)
        (x1, y1) = ((WIDTH - width) / 2, (HEIGHT - height) / 2)
        draw.rectangle(((x1, y1), (WIDTH - x1, (HEIGHT - y1))), width=1, fill=fill)
        font = ImageFont.truetype("arial.ttf", 30)
        # decrease the font size until it all fits
        display_text = ""
        # add new lines when necessary
        for word in text.split(" "):
            if draw.multiline_textsize(display_text + word + " ", font=font)[0] > width:
                # too long
                # add new line
                if draw.multiline_textsize(display_text + "\n" + word, font=font)[0] > width:
                    # the word is just too long
                    raise Exception("one word is too long to display in one line")
                display_text = display_text + "\n" + word + " "
            else:
                display_text = display_text + word + " "
        if draw.multiline_textsize(display_text, font=font)[0] > width or \
                draw.multiline_textsize(display_text, font=font)[1] > height:
            raise Exception("text is too long to display")
        draw.multiline_text((x1, y1), display_text, font=font)
        self.popup = True
        if popup_close_event is not None:
            self.popup_close_event = popup_close_event
        self.display.display(self.image)

    def text_input(self, character: str):
        if character == "PASSWORD_MANAGER_ENABLE":
            character = chr(7)
        # make sure the character is at least 1 character long
        if len(character) < 1:
            raise RuntimeError("parameter character must at least one character")
        # if the character is longer than one character call the function with each character seperate
        elif len(character) > 1:
            for i in range(len(character)):
                self.text_input(character[i])
            return
        # if popup is shown right now display the gui again and set popup to false
        if self.popup is True:
            self.popup = False
            if self.popup_close_event is None:
                self.__update_display()
            else:
                self.popup_close_event()
            return

        if character == chr(7):
            self.show_popup("tastatur aktiv", fill="green")
        # case up
        if character == chr(17):
            self.scroll(-1)
        # case down
        elif character == chr(18):
            self.scroll(1)
        # case right
        elif character == chr(19):
            self.scroll_vertical(-1)
        # case left
        elif character == chr(20):
            self.scroll_vertical(1)
        # case enter
        elif character == "\n":
            # check if selected element is of type button
            if isinstance(self.elements[self.position], ButtonElement):
                # call the button callback
                self.elements[self.position].on_click()
                # refresh the display
            # check if selected element is of type text box
            elif isinstance(self.elements[self.position], TextBoxElement):
                # call the text box on enter callback
                self.elements[self.position].on_enter()
                # refresh the display
            # else do nothing
        # case backspace
        elif character == "\b":
            # check if selected element is of type textbox and and if the value is at least of length 1 so there can be deleted one character
            if isinstance(self.elements[self.position], TextBoxElement) and len(
                    self.elements[self.position].value) >= 1:
                # check if the text box is not readonly
                if not self.elements[self.position].readonly:
                    # remove the last character
                    self.elements[self.position].value = self.elements[self.position].value[:-1]
                    # call the on change callback
                    self.elements[self.position].on_change()
                    # refresh the display
                    self.__update_display()
        # default case
        else:
            # check if selected element is of type textbox
            if isinstance(self.elements[self.position], TextBoxElement):
                # check if text box is not readonly
                if not self.elements[self.position].readonly:
                    # add the character
                    self.elements[self.position].value += character
                    # call the on change callback
                    self.elements[self.position].on_change()
                    # refresh the display
                    self.__update_display()
            # else do nothing
        return

    def show(self):
        self.__update_display()
        return

    def __update_display(self):
        image = Image.new("RGB", (240, 240))
        if self.position == 0 and isinstance(self.elements[0], TextFieldElement) and len(self.elements) > 1:
            self.position = 1
        # choose the three elements to display
        display_elements = []
        if self.position == 0:
            display_elements = self.elements.copy()[:3]
            for i in range(3):
                if i < len(display_elements):
                    display_elements[i].selected = False
            # set the selected element to the first selectable element
            for i in range(3):
                if i < len(display_elements):
                    if isinstance(display_elements[i], ButtonElement) or isinstance(display_elements[i],
                                                                                    TextBoxElement):
                        display_elements[i].selected = True
                        break
                if i == 2:
                    raise RuntimeError("at least one Element must be of type ButtonElement or TextBoxElement")

        # position is on the last element
        elif self.position == len(self.elements) - 1:
            display_elements = self.elements.copy()[-3:]
            # set the selected element to the last element
            # set all elements to selected false
            for i2 in range(3):
                if i2 < len(display_elements):
                    display_elements[i2].selected = False
            display_elements[-1].selected = True

        else:
            for i in range(3):
                if self.position + i - 1 < len(self.elements):
                    display_elements.append(self.elements[self.position + i - 1])
                    if i == 1:
                        display_elements[i].selected = True
                    else:
                        display_elements[i].selected = False

        # display the three elements
        for i in range(3):
            if i < len(display_elements):
                image.paste(display_elements[i].draw(), (0, 0 + 80 * i, 240, 80 + 80 * i))
        self.image = image
        self.display.display(self.image)
        # todo should test or at least go through all the code again
        return

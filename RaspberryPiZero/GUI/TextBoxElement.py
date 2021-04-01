from .Element import Element
from .Constants import ELEMENT_HEIGHT_CONSTANT, ELEMENT_WIDTH_CONSTANT
from PIL import Image, ImageDraw, ImageFont
import math
import queue


# static function for drawing a rounded rectangle
def _TextBoxElement__rounded_rectangle(radius: int, margin: int, width: int, height: int, draw: ImageDraw):
    # draw left upper rounded edge
    draw.arc(((0 + margin - 1, 0 + margin - 1), (0 + margin + radius - 1, 0 + margin + radius - 1)), 180, 270)
    # draw left lower rounded edge
    draw.arc(((0 + margin - 1, height - margin - radius - 1), (0 + margin + radius - 1, height - margin - 1)), 90,
             180)
    # draw right lower rounded edge
    draw.arc(
        ((width - margin - radius - 1, height - margin - radius - 1), (width - margin - 1, height - margin - 1)), 0,
        90)
    # draw right upper rounded edge
    draw.arc(((width - margin - radius - 1, 0 + margin - 1), (width - margin - 1, 0 + margin + radius - 1)), 270, 0)

    # draw upper line
    draw.line(((0 + margin + radius / 2 - 1, 0 + margin - 1), (width - margin - radius / 2 - 1, 0 + margin - 1)))
    # draw lower line
    draw.line(((0 + margin + radius / 2 - 1, height - margin - 1),
               (width - margin - radius / 2 - 1, height - margin - 1)))
    # draw left line
    draw.line(((0 + margin - 1, 0 + margin + radius / 2 - 1), (0 + margin - 1, height - margin - radius / 2 - 1)))
    # draw right line
    draw.line(
        ((width - margin - 1, 0 + margin + radius / 2 - 1), (width - margin - 1, height - margin - radius / 2 - 1)))


class TextBoxElement(Element):
    onchangecallback: callable = None
    onentercallback: callable = None
    placeholder: str = ""
    obfuscated: bool = False
    readonly: bool = False
    scroll_position: int = 0

    def __init__(self, text: str, onchangecallback: callable = None, onentercallback: callable = None,
                 placeholder: str = "", obfuscated: bool = False, readonly: bool = False):
        # def __init__(self, onchangecallback, placeholder: str, text: str, obfuscated: bool):
        # if the callback is None assign it the empty callback from the parent class
        if onchangecallback is not None:
            self.onchangecallback = onchangecallback
        if onentercallback is not None:
            self.onentercallback = onentercallback
        self.placeholder = placeholder
        self.value = text
        self.obfuscated = obfuscated
        self.readonly = readonly
        return

    def scroll(self, diff: int):
        self.scroll_position = self.scroll_position - diff
        # if the scroll position is greater than 0 set it back to 0
        if self.scroll_position > 0:
            self.scroll_position = 0
        # if the scroll position is greater than the value allows set it to the greatest value possible
        elif self.scroll_position * -1 >= len(self.value):
            self.scroll_position = len(self.value) - 1

    def draw(self) -> Image.Image:
        if self.value is None:
            self.value = ""

        # get the width and height of the element image
        (ELEMENT_WIDTH, ELEMENT_HEIGHT) = (ELEMENT_WIDTH_CONSTANT(), ELEMENT_HEIGHT_CONSTANT())
        # create new image
        image = Image.new("RGB", (ELEMENT_WIDTH, ELEMENT_HEIGHT))
        # create new draw object
        draw = ImageDraw.Draw(image)

        if self.selected:
            draw.rectangle(((0, 0), (ELEMENT_WIDTH - 1, ELEMENT_HEIGHT - 1)), width=0, fill="Grey")

        # draw rounded rectangle
        radius = 50
        margin = 10
        __rounded_rectangle(radius, margin, ELEMENT_WIDTH, ELEMENT_HEIGHT, draw)

        # calculate the coordinate of the text
        (x, y) = (0 + margin + int(math.floor(0.29 * radius)), 0 + margin + int(math.floor(0.29 * radius)))
        # calculate the height and width of the text in the rounded rectangle
        (width, height) = (ELEMENT_WIDTH - int(math.floor(2 * 0.29 * radius)) - margin,
                           ELEMENT_HEIGHT - int(math.floor(2 * 0.29 * radius)) - margin)

        # draw the text
        font = ImageFont.truetype("arial.ttf", 30)
        # if the value of the text is empty show the placeholder
        fill = "white"
        if self.value == "" and self.placeholder != "":
            fill = "blue"

        text: str = ""
        if self.obfuscated and self.value != "":
            text = "*" * len(self.value)
        elif self.value == "" and self.placeholder != "":
            text = self.placeholder
        else:
            text = self.value
        # if the text is too long for the textbox remove the first characters until it fits
        (text_width, text_height) = draw.textsize(text, font=font)

        # if the text doesnt fit show a truncated text
        if text_width > width:
            # temp_text = currently selected character
            temp_text = text[len(text) - 1 + self.scroll_position]
            # left_queue = characters left of the selected character
            left_queue = queue.Queue()
            # right_queue = characters right of the selected character
            right_queue = queue.Queue()
            # assign the characters as described on the declaration
            if len(text) - 1 + self.scroll_position > 0:
                for i in reversed(range(len(text) - 1 + self.scroll_position)):
                    left_queue.put(text[i])
            if len(text) + self.scroll_position < len(text):
                for i in range(len(text) + self.scroll_position, len(text)):
                    right_queue.put(text[i])
            temp_text2 = temp_text
            # add ... on either side if the corresponding queue is not empty
            if not left_queue.empty():
                temp_text2 = "..." + temp_text2
            if not right_queue.empty():
                temp_text2 = temp_text2 + "..."
            # calculate the text width
            (text_width, text_height) = draw.textsize(temp_text2)
            # add one character to the left and right until it fits no more in the textbox (including the ...)
            while text_width < width and (not left_queue.empty() or not right_queue.empty()):
                text = temp_text2
                temp_text2 = ""
                # if the queue is not empty get one character of the queue and add it to the text
                if not left_queue.empty():
                    temp_text = left_queue.get() + temp_text
                # if the queue is not empty get one character of the queue and add it to the text
                if not right_queue.empty():
                    temp_text = temp_text + right_queue.get()
                # if the queue is not empty add a ...
                if not left_queue.empty():
                    temp_text2 = "..." + temp_text
                else:
                    temp_text2 = temp_text
                # if the queue is not empty add a ...
                if not right_queue.empty():
                    temp_text2 = temp_text2 + "..."
                # calculate the new text width
                (text_width, text_height) = draw.textsize(temp_text2, font=font)

        # draw the text on the image
        draw.text((x, y), text, font=font, fill=fill)

        # return the generated image
        return image

    def on_change(self):
        # if the scroll position is greater than the value allows set it to the greatest value possible
        if self.scroll_position * -1 >= len(self.value):
            self.scroll_position = len(self.value) - 1
        # call the callback if one is set
        if self.onchangecallback is not None:
            self.onchangecallback(self)
        return

    def on_enter(self):
        # call the callback if one is set
        if self.onentercallback is not None:
            self.onentercallback(self)
        return

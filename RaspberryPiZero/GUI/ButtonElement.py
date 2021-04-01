from .Element import Element
from PIL import Image, ImageDraw, ImageFont
from .Constants import ELEMENT_WIDTH_CONSTANT, ELEMENT_HEIGHT_CONSTANT


class ButtonElement(Element):
    onclickcallback: callable = None
    argument = None

    def __init__(self, text: str, onclickcallback: callable = None, argument=None):
        # if the callback is None assign it the empty callback from the parent class
        if onclickcallback is None:
            self.onclickcallback = lambda: None
        else:
            self.onclickcallback = onclickcallback
        self.value = text
        self.argument = argument

    def draw(self) -> Image.Image:
        (ELEMENT_WIDTH, ELEMENT_HEIGHT) = (ELEMENT_WIDTH_CONSTANT(), ELEMENT_HEIGHT_CONSTANT())
        # create image for drawing
        image = Image.new("RGB", (ELEMENT_WIDTH, ELEMENT_HEIGHT))
        draw = ImageDraw.Draw(image)
        # fill the rectangle if the element is selected
        # todo implement the rectangle dependent from the element width and height
        if self.selected:
            draw.rectangle(((10, 10), (229, 70)), width=2, fill="Gray")
        else:
            draw.rectangle(((10, 10), (229, 70)), width=2)
        # create the font
        font = ImageFont.truetype("arial.ttf", 60)
        # margin values
        margin = [10, 10, 10, 10]
        margin_top, margin_right, margin_bottom, margin_left = margin
        # padding values
        padding = [3, 3, 3, 3]
        padding_top, padding_right, padding_bottom, padding_left = padding
        # calculate the width and height for the text
        width, height = (ELEMENT_WIDTH - margin_left - margin_right - padding_left - padding_right,
                         ELEMENT_HEIGHT - margin_top - margin_bottom - padding_top - padding_bottom)
        # calculate the resulting size
        width_result, height_result = draw.textsize(self.value, font=font)
        # make the font size smaller until it fits into the button
        while width_result > width:
            # decrease the size by one
            font = ImageFont.truetype("arial.ttf", font.size - 1)
            # if the font size is smaller than 10 it is too small to read
            # todo test real font size; 10 is just guessed right now
            if font.size <= 10:
                raise RuntimeError("font size too small")
            # calculate the resulting size
            width_result, height_result = draw.textsize(self.value, font=font)
        # draw the text
        draw.text(((width - width_result) / 2 + margin_left + padding_left,
                   (height - height_result) / 2 + margin_top + padding_top), self.value, font=font)

        # return the created image
        return image

    def on_click(self):
        if self.onclickcallback is not None:
            self.onclickcallback(self)
        return

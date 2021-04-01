from .Element import Element
from PIL import Image, ImageDraw, ImageFont
from .Constants import ELEMENT_WIDTH_CONSTANT, ELEMENT_HEIGHT_CONSTANT


class TextFieldElement(Element):
    def __init__(self, text: str):
        self.value = text

    def draw(self) -> Image.Image:
        (ELEMENT_WIDTH, ELEMENT_HEIGHT) = (ELEMENT_WIDTH_CONSTANT(), ELEMENT_HEIGHT_CONSTANT())
        image = Image.new("RGB", (ELEMENT_WIDTH, ELEMENT_HEIGHT))
        draw = ImageDraw.Draw(image)

        # create the font
        font = ImageFont.truetype("arial.ttf", 60)
        # padding values
        padding = [0, 10, 0, 10]
        padding_top, padding_right, padding_bottom, padding_left = padding
        # calculate the width and height for the text
        width, height = (ELEMENT_WIDTH - padding_right - padding_left,
                         ELEMENT_HEIGHT - 1 - padding_top - padding_bottom)
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
        draw.text(((width - width_result) / 2 + padding_left,
                   (height - height_result) / 2 + padding_top), self.value, font=font)
        draw.line(((0, 79), (239, 79)), width=1)
        return image

from PIL import Image


class Element:
    selected: bool = False
    value: str = ""

    def draw(self) -> Image.Image:
        raise RuntimeError("element must cannot be of type Element but of a child Element")

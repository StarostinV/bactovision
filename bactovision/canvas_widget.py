from pathlib import Path
from io import BytesIO
import base64
from PIL import Image

import anywidget
import traitlets
import numpy as np

import matplotlib.cm as cm

from bactovision.image_processing import normalize_image


class CanvasWidget(anywidget.AnyWidget):
    # js code
    _esm = Path(__file__).parent / 'canvas.js'

    # image
    image_data = traitlets.Unicode().tag(sync=True)

    # annotation
    brush_size = traitlets.Float(5).tag(sync=True)  # Default brush size set to 10
    mode = traitlets.Unicode("add-segments").tag(sync=True)
    annotated_image = traitlets.Unicode("").tag(sync=True)

    # grid
    grid_num_x = traitlets.Int(12).tag(sync=True)
    grid_num_y = traitlets.Int(8).tag(sync=True)
    hide_grid = traitlets.Bool().tag(sync=True)
    change_grid = traitlets.Bool().tag(sync=True)

    # grid padding. These parameters should not be controlled by setting values,
    # since the change will not be reflected on a canvas immediately.
    pad_top = traitlets.Float(50).tag(sync=True)
    pad_bottom = traitlets.Float(60).tag(sync=True)
    pad_left = traitlets.Float(90).tag(sync=True)
    pad_right = traitlets.Float(50).tag(sync=True)

    def set_image(self, image_array: np.array, cmap: str = 'YlGnBu'):
        self.image_data = array2str(image_array, cmap=cmap)

    def set_annotation(self, mask):
        self.annotated_image = array2str(mask2red(mask))

    def get_annotation(self):
        return str2array(self.annotated_image)

    def get_grid_dict(self):
        return {
            'num_x': int(self.grid_num_x),
            'num_y': int(self.grid_num_y),
            'pad_top': float(self.pad_top),
            'pad_bottom': float(self.pad_bottom),
            'pad_left': float(self.pad_left),
            'pad_right': float(self.pad_right),
        }


def str2array(base64_str: str):
    base64_str = base64_str.split(",")[1] if "," in base64_str else base64_str
    image_bytes = base64.b64decode(base64_str)
    return np.array(Image.open(BytesIO(image_bytes)))


def array2str(arr: np.ndarray, cmap: str = 'YlGnBu'):

    if len(arr.shape) == 2:
        arr = cm.get_cmap(cmap)(arr)

    arr = (normalize_image(arr) * 255).astype('uint8')

    assert len(arr.shape) == 3

    mode = 'RGB' if arr.shape[-1] == 3 else 'RGBA'

    image = Image.fromarray(arr, mode)  # Use 'RGBA' if your array includes an alpha channel

    # Save the PIL Image to a bytes buffer
    buffer = BytesIO()
    image.save(buffer, format="PNG")  # You can change 'PNG' to 'JPEG' or other formats depending on your needs
    buffer.seek(0)

    # Encode the bytes buffer to base64
    image_base64 = base64.b64encode(buffer.read())

    # Decode bytes to a string and format for use as a data URL if needed
    image_base64_str = "data:image/png;base64," + image_base64.decode()

    return image_base64_str


def mask2red(mask):
    annotation = ((mask > 0).astype(np.uint8) * 255)[..., None].repeat(4, 2)
    annotation[(mask > 0), 0] = 255
    annotation[(mask > 0), 3] = 255 // 2

    annotation[(mask == 0), 0] = 0
    annotation[(mask == 0), 3] = 0

    annotation[..., [1, 2]] = 0
    return annotation

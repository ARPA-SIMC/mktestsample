from __future__ import annotations
import io
import logging
from typing import TYPE_CHECKING, List

from . import common

if TYPE_CHECKING:
    import PIL

log = logging.getLogger("jpeg")


def replace_data(img: PIL.Image) -> PIL.Image:
    """
    Replace all data in an image with zeroes
    """
    # Import here to avoid depending on eccodes for other unrelated features
    from PIL import Image

    # Replace contents with zeroes
    if img.mode in ("1", "L", "P", "I", "F"):
        sample = 0
    elif img.mode in ("RGB", "YCbCr", "LAB", "HSV"):
        sample = (0, 0, 0)
    elif img.mode in ("RGBA", "CYMK"):
        sample = (0, 0, 0, 0)

    new_img = Image.new(img.mode, img.size, sample)
    return new_img


def minimize_jpeg_file(fname: str) -> bytes:
    """
    Replace all data in a JPEG file, returning the resulting encoded data.

    Note that the result is still heavily compressible: I could not find a way
    to minimize jpeg further without cropping
    """
    # Import here to avoid depending on eccodes for other unrelated features
    from PIL import Image

    # Also available:
    # https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.frombytes
    img = Image.open(fname)
    orig_exif = img.info["exif"]

    img = replace_data(img)

    with io.BytesIO() as outfd:
        img.save(outfd,
                 format="JPEG", quality=0, subsampling=2, optimize=True,
                 quantization=[[1000]*64, [1000]*64],
                 exif=orig_exif)
        return outfd.getvalue()


class MinimizeJPEG(common.MinimizeFile):
    def make_new_contents(self) -> List[bytes]:
        # Read GRIB contents, computing minified versions
        new_contents = [minimize_jpeg_file(self.fname)]

        return new_contents

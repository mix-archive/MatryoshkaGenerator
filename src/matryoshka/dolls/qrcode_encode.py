import io
import itertools
import math
from base64 import b64decode, b64encode

import pyzbar.pyzbar as pyzbar
from PIL import Image
from qrcode import ERROR_CORRECT_M
from qrcode.main import QRCode

from .base import DollError, DollsBase


class QRCodeDoll(DollsBase):
    @property
    def maximum_capacity(self) -> int:
        return 1200

    def encode(self, secret_text: bytes) -> bytes:
        qr = QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=1,
            border=1,
        )
        qr.add_data(b64encode(secret_text))
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_binarized = Image.open(buf).convert("1")
        bits: list[int] = []
        for x, y in itertools.product(
            range(image_binarized.width), range(image_binarized.height)
        ):
            bits.append(image_binarized.getpixel((x, y)) & 1)
        return "".join(map(str, bits)).encode()

    def decode(self, data: bytes) -> bytes:
        bits_array = [int(bit, 2) for bit in data.decode()]
        size = math.isqrt(len(bits_array))
        image = Image.new("1", (size, size))

        for x, y in itertools.product(range(size), range(size)):
            image.putpixel((x, y), bits_array[x * size + y])
        pyzbar_data = pyzbar.decode(image)

        if not pyzbar_data:
            human_readable = ""
            for y in range(size):
                for x in range(size):
                    human_readable += "█" if image.getpixel((x, y)) else " "
                human_readable += "\n"
            raise DollError("No QR code found" + "\n" + human_readable)

        return b64decode(pyzbar_data[0].data)

import io
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
        return "".join(str(i & 1) for i in image_binarized.getdata()).encode()

    def decode(self, data: bytes) -> bytes:
        size = math.isqrt(len(data))
        image = Image.new("1", (size, size))

        image.putdata([int(bit, 2) for bit in data.decode()])
        pyzbar_data = pyzbar.decode(image)

        if not pyzbar_data:
            human_readable = ""
            for i, pixel in enumerate(image.getdata()):
                human_readable += "\u2588" if pixel else "\u2591"
                if i % size == size - 1:
                    human_readable += "\n"
            raise DollError("No QR code found" + "\n" + human_readable)

        return b64decode(pyzbar_data[0].data)

import io
import math

from PIL import Image

from .base import DollsBase


class RGBAImageBytesDoll(DollsBase):
    @property
    def maximum_capacity(self) -> int:
        return (1 << 32) - 4  # 4 bytes for the size of the data

    @staticmethod
    def _find_size_factor(data_size: int) -> tuple[int, int]:
        max_factor = math.ceil(math.sqrt(data_size))
        for x in reversed(range(2, max_factor + 1)):
            if data_size % x == 0:
                return x, data_size // x
        return (max_factor, max_factor)

    def encode(self, secret_text: bytes) -> bytes:
        mode_bands = Image.getmodebands("RGBA")
        data_size = len(secret_text)
        width, height = self._find_size_factor(data_size)
        encoded_text = data_size.to_bytes(4, "big") + secret_text
        image = Image.new("RGBA", (width, height))
        image.putdata(
            [
                tuple(
                    encoded_text[offset : offset + mode_bands].ljust(
                        mode_bands, b"\x00"
                    )
                )
                for offset in range(0, len(encoded_text), mode_bands)
            ]  # type: ignore
        )

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

    def decode(self, data: bytes) -> bytes:
        image = Image.open(io.BytesIO(data))
        image_bytes = bytes(char for pixel in image.getdata() for char in pixel)
        data_size = int.from_bytes(image_bytes[:4], "big")
        return bytes(image_bytes[4 : 4 + data_size])

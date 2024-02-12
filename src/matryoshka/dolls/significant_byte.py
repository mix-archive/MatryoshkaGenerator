import io
import itertools
from pathlib import Path

from PIL import Image

from .base import DollError, DollsBase


class _SignificantByteDoll(DollsBase):
    def __init__(
        self,
        image_path: Path = Path(__file__).parent / "significant_byte_image.jpg",
    ):
        self.image_path = image_path

    @property
    def maximum_capacity(self) -> int:
        image_copy = self._image_copy()
        return min(
            (image_copy.width * image_copy.height * len(image_copy.getbands())) // 8
            - 4,  # minus 4 bytes for the length of the secret text
            1 << 32,
        )

    def _hide(self, pixel: int, bit: int) -> int:
        raise NotImplementedError

    def _extract(self, pixel: int) -> int:
        raise NotImplementedError

    def _image_copy(self):
        return Image.open(self.image_path).convert("RGBA").copy()

    def encode(self, secret_text: bytes):
        encode_text = len(secret_text).to_bytes(4, "big") + secret_text
        encode_text_generator = (
            int(bit, 2) for bit in "".join(f"{c:08b}" for c in encode_text)
        )

        image_copy = self._image_copy()
        image_copy.putdata(
            [
                tuple(
                    self._hide(pixel, next(encode_text_generator, 0)) for pixel in data
                )
                for data in image_copy.getdata()
            ]  # type: ignore
        )

        buf = io.BytesIO()
        image_copy.save(buf, format="PNG")
        return buf.getvalue()

    def decode(self, data: bytes):
        buf = io.BytesIO(data)
        image = Image.open(buf)

        secret_text_bits = map(
            self._extract, itertools.chain.from_iterable(image.getdata())
        )
        length = int.from_bytes(
            bytes(
                int("".join(str(next(secret_text_bits)) for _ in range(8)), 2)
                for _ in range(4)
            ),
            "big",
        )

        if length > self.maximum_capacity:
            raise DollError("The length of the secret text is too long")

        return bytes(
            int("".join(str(next(secret_text_bits)) for _ in range(8)), 2)
            for _ in range(length)
        )


class MostSignificantByteDoll(_SignificantByteDoll):
    def _hide(self, pixel: int, bit: int) -> int:
        return (pixel & 0b01111111) | (bit << 7)

    def _extract(self, pixel: int) -> int:
        return pixel >> 7


class LeastSignificantByteDoll(_SignificantByteDoll):
    def _hide(self, pixel: int, bit: int) -> int:
        return (pixel & 0b11111110) | bit

    def _extract(self, pixel: int) -> int:
        return pixel & 0b00000001

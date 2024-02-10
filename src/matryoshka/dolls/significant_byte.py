import io
import itertools
from pathlib import Path

from PIL import Image

from .base import DollsBase


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
            image_copy.width * image_copy.height * len(image_copy.getbands())
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
        for x, y in itertools.product(
            range(image_copy.width), range(image_copy.height)
        ):
            pixel: list[int] = [*image_copy.getpixel((x, y))]
            for i, data in enumerate(pixel):
                bit = next(encode_text_generator, 0)
                pixel[i] = self._hide(data, bit)
            image_copy.putpixel((x, y), tuple(pixel))  # type: ignore

        buf = io.BytesIO()
        image_copy.save(buf, format="PNG")
        return buf.getvalue()

    def decode(self, data: bytes):
        secret_text_bits: list[int] = []
        buf = io.BytesIO(data)
        image = Image.open(buf)

        for x, y in itertools.product(range(image.width), range(image.height)):
            pixel: list[int] = [*image.getpixel((x, y))]
            for i in pixel:
                secret_text_bits.append(self._extract(i))
        length, remainder = divmod(len(secret_text_bits), 8)
        decoded_text = bytes(
            int("".join(map(str, secret_text_bits[i : i + 8])), 2)
            for i in range(0, length * 8, 8)
        )
        decoded_length = int.from_bytes(decoded_text[:4], "big")
        return decoded_text[4 : 4 + decoded_length]


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

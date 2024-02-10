from .base import DollsBase


class _ReverseEncoding(DollsBase):
    @property
    def maximum_capacity(self) -> int:
        return 0


class BitReverseDoll(_ReverseEncoding):
    def encode(self, secret_text: bytes) -> bytes:
        return bytes(int(f"{c:08b}"[::-1], 2) for c in secret_text)

    def decode(self, data: bytes) -> bytes:
        return bytes(int(f"{c:08b}"[::-1], 2) for c in data)


class ByteReverseDoll(_ReverseEncoding):
    def encode(self, secret_text: bytes) -> bytes:
        return secret_text[::-1]

    def decode(self, data: bytes) -> bytes:
        return data[::-1]

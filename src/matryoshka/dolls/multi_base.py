from base64 import (
    b16decode,
    b16encode,
    b32decode,
    b32encode,
    b64decode,
    b64encode,
    b85decode,
    b85encode,
)
from binascii import Error as EncodingError
from typing import Callable, Literal

from .base import DollError, DollsBase

SupportedBase = Literal[32, 64, 85, 58]
EncodeFunction = Callable[[bytes], bytes]


class _MultiBaseEncoding(DollsBase):
    decode_func: Callable[[bytes], bytes]
    encode_func: Callable[[bytes], bytes]

    @property
    def maximum_capacity(self) -> int:
        return 0

    def encode(self, secret_text: bytes) -> bytes:
        try:
            return self.encode_func(secret_text)
        except EncodingError as e:
            raise DollError("failed to encode") from e

    def decode(self, data: bytes) -> bytes:
        try:
            return self.decode_func(data)
        except (EncodingError, ValueError) as e:
            raise DollError("failed to decode") from e


class Base16Doll(_MultiBaseEncoding):
    decode_func = staticmethod(b16decode)
    encode_func = staticmethod(b16encode)


class Base32Doll(_MultiBaseEncoding):
    decode_func = staticmethod(b32decode)
    encode_func = staticmethod(b32encode)


class Base64Doll(_MultiBaseEncoding):
    decode_func = staticmethod(b64decode)
    encode_func = staticmethod(b64encode)


class Base85Doll(_MultiBaseEncoding):
    decode_func = staticmethod(b85decode)
    encode_func = staticmethod(b85encode)

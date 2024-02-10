import io
import random
import time
from logging import getLogger
from pathlib import Path

import pyzipper

from .base import DollError, DollsBase

logger = getLogger(__name__)


class WeakZipDoll(DollsBase):
    def __init__(self, dictionary: Path = Path(__file__).parent / "weak_zip_dict.txt"):
        self.dictionary = [
            stripped
            for line in dictionary.read_text().splitlines()
            if (stripped := line.strip())
        ]

    @property
    def maximum_capacity(self) -> int:
        return 0

    def encode(self, secret_text: bytes):
        password = random.choice(self.dictionary)
        filename = random.randbytes(5).hex() + ".txt"

        zip_data = io.BytesIO()
        with pyzipper.AESZipFile(
            zip_data,
            "w",
            compression=pyzipper.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        ) as zip_ref:
            zip_ref.setpassword(password.encode())
            zip_ref.writestr(filename, secret_text)

        return zip_data.getvalue()

    def _brute_force(self, data: bytes) -> tuple[str, bytes]:
        for password in self.dictionary:
            try:
                with pyzipper.AESZipFile(io.BytesIO(data)) as zip_ref:
                    zip_ref.setpassword(password.encode())
                    secret_content = zip_ref.read(zip_ref.namelist()[0])
                    return password, secret_content
            except RuntimeError:
                pass
        raise DollError("Password not found")

    def decode(self, data: bytes):
        begin = time.time()
        _, secret_text = self._brute_force(data)
        delta = (time.time() - begin) * 1000
        logger.debug("Brute force took %.2fms", delta)
        return secret_text

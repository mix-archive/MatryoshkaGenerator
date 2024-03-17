import io
import itertools
import random
import string
import threading
import time
from collections import deque
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from logging import getLogger
from typing import ClassVar

import pyzipper

from .base import DollError, DollsBase

logger = getLogger(__name__)


class WeakZipDoll(DollsBase):
    cache_size: ClassVar[int] = 100

    historical_password_cache: ClassVar[deque[str]] = deque(maxlen=cache_size)
    cache_mutation_lock = threading.Lock()

    def __init__(self, charset: str = string.digits, length: int = 5):
        super().__init__()
        self.charset = charset
        self.length = length

    @property
    def maximum_capacity(self) -> int:
        return 0

    def encode(self, secret_text: bytes):
        password = "".join(random.choices(self.charset, k=self.length))
        filename = random.randbytes(self.length).hex() + "brute_plz.txt"

        zip_data = io.BytesIO()
        with pyzipper.AESZipFile(
            zip_data,
            "w",
            compression=pyzipper.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        ) as zip_ref:
            zip_ref.setpassword(password.encode())
            zip_ref.writestr(filename, secret_text)

        with type(self).cache_mutation_lock:
            type(self).historical_password_cache.append(password)
        return zip_data.getvalue()

    @staticmethod
    def _brute_force_worker(data: bytes, password: str):
        buf = io.BytesIO(data)
        try:
            with pyzipper.AESZipFile(buf) as zip_ref:
                zip_ref.setpassword(password.encode())
                secret_content = zip_ref.read(zip_ref.namelist()[0])
                return password, secret_content
        except RuntimeError:
            return password, None
        except Exception as e:
            logger.debug("Brute force failed with password=%s, error=%s", password, e)
            return password, None

    def _brute_force(self, data: bytes) -> tuple[str, bytes]:
        if type(self).historical_password_cache:
            with type(self).cache_mutation_lock:
                historical_password = [*type(self).historical_password_cache]
            for password in historical_password:
                password, content = self._brute_force_worker(data, password)
                if content:
                    return password, content
            logger.warning("Historical password cache not hit")
        with ProcessPoolExecutor() as executor:
            for password, content in executor.map(
                partial(self._brute_force_worker, data),
                map("".join, itertools.product(self.charset, repeat=self.length)),
                chunksize=100,
            ):
                if content:
                    return password, content
        raise DollError("Password not found")

    def decode(self, data: bytes):
        begin = time.time()
        _, secret_text = self._brute_force(data)
        delta = (time.time() - begin) * 1000
        logger.debug("Brute force took %.2fms", delta)
        return secret_text

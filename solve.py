import re
import sys
from base64 import decodebytes

import pwn as p
from matryoshka.dolls.base import DollError, DollsBase
from matryoshka.dolls.multi_base import Base16Doll, Base32Doll, Base64Doll, Base85Doll
from matryoshka.dolls.qrcode_encode import QRCodeDoll
from matryoshka.dolls.reverse import BitReverseDoll, ByteReverseDoll
from matryoshka.dolls.rgb_bytes import RGBAImageBytesDoll
from matryoshka.dolls.significant_byte import (
    LeastSignificantByteDoll,
    MostSignificantByteDoll,
)
from matryoshka.dolls.weak_zip import WeakZipDoll


def decode(
    data: bytes,
    round: int = 1,
    result_regex=rb"flag{.*?}",
    accepted_dolls: tuple[type[DollsBase], ...] = (),
    length_threshold: int = 10,
):
    def prefixed_print(*args):
        p.log.info(" ".join(["--" * round + ">", *map(str, args)]))

    prefixed_print("entering round", round)
    attempts: list[type[DollsBase]] = []
    if data.startswith(b"PK"):  # PK is the magic number for ZIP files
        attempts.append(WeakZipDoll)
    if data.startswith(b"\x89PNG"):  # PNG magic number
        attempts.append(RGBAImageBytesDoll)
        attempts.append(LeastSignificantByteDoll)
        attempts.append(MostSignificantByteDoll)
    if data.isascii():  # ASCII
        charset = {bytes([c]) for c in data}
        if charset == {b"0", b"1"}:
            attempts.append(QRCodeDoll)
        else:
            attempts.append(Base16Doll)
            attempts.append(Base32Doll)
            attempts.append(Base64Doll)
            attempts.append(Base85Doll)
    attempts.append(BitReverseDoll)
    attempts.append(ByteReverseDoll)

    attempts = [attempt for attempt in attempts if attempt not in accepted_dolls]
    for attempt in attempts:
        prefixed_print(f"trying {attempt.__name__}")
        try:
            result = attempt().decode(data)
        except DollError as e:
            prefixed_print(f"failed {attempt.__name__}: {e}")
            continue
        if len(result) < length_threshold:
            prefixed_print(f"failed {attempt.__name__}: length not accepted")
            continue
        if re.search(result_regex, result, re.DOTALL):
            prefixed_print(f"success {attempt.__name__}: {result}")
            return result
        prefixed_print("result not clear, recursive decode begin")
        result = decode(result, round + 1, result_regex, (*accepted_dolls, attempt))
        if result:
            return result
    prefixed_print("round failed")
    return None


_, host, port = sys.argv

s = p.remote(host, port)
s.recvuntil(b"encode")
s.sendline(b"encode")

while True:
    data = s.recvuntil(b"-----END MATRYOSHKA MESSAGE-----")
    round_data = re.search(rb"Round (\d+)/(\d+)", data)
    assert round_data
    round = int(round_data.group(1))
    total_rounds = int(round_data.group(2))
    p.log.info(f"Round {round}/{total_rounds}")

    data_chunk = re.search(
        b"-----BEGIN MATRYOSHKA MESSAGE-----\n(.*)\n-----END MATRYOSHKA MESSAGE-----",
        data,
        re.DOTALL,
    )
    assert data_chunk
    data = decode(decodebytes(data_chunk.group(1)))
    assert data
    s.sendline(data)
    if round == total_rounds:
        break

s.interactive()

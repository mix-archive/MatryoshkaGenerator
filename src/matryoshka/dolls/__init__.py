from .multi_base import Base16Doll, Base32Doll, Base64Doll, Base85Doll
from .qrcode_encode import QRCodeDoll
from .reverse import BitReverseDoll, ByteReverseDoll
from .rgb_bytes import RGBAImageBytesDoll
from .significant_byte import LeastSignificantByteDoll, MostSignificantByteDoll
from .weak_zip import WeakZipDoll

dolls_registry = (
    (Base16Doll, Base32Doll, Base64Doll, Base85Doll),
    (RGBAImageBytesDoll,),
    (BitReverseDoll, ByteReverseDoll),
    (WeakZipDoll,),
    (QRCodeDoll,),
    (MostSignificantByteDoll, LeastSignificantByteDoll),
)

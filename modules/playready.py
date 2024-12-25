from construct import Struct, Const, Int8ub, Bytes, Int32ub, Int16ub, Optional, Padded, Flag, BitStruct, Padding, If, this
from enum import IntEnum  # Import IntEnum

class BaseDevice:
    class Types(IntEnum):
        EDGE = 1
        ANDROID = 2

class PlayReadyDeviceStruct(BaseDevice):
    PlayReadyDeviceStructVersion = Struct(
        "signature" / Const(b"PRD"),
        "version" / Int8ub,
        "group_key" / Bytes(96),
        "encryption_key" / Bytes(96),
        "signing_key" / Bytes(96),
        "group_certificate_length" / Int32ub,
        "group_certificate" / Bytes(this.group_certificate_length)
    )
from construct import Struct, Const, Int8ub, Bytes, Int32ub, Int16ub, Optional, Padded, Flag, BitStruct, Padding, If, this
from construct import Enum as CEnum
from enum import IntEnum


class BaseDevice:
    class Types(IntEnum):
        CHROME = 1
        ANDROID = 2
        
class WidevineDeviceStruct(BaseDevice):
    WidevineDeviceStructVersion = Struct(
        "signature" / Const(b"WVD"),
        "version" / Const(Int8ub, 2),
        "type_" / CEnum(
            Int8ub,
            **{t.name: t.value for t in BaseDevice.Types}  # Iterate over BaseDevice.Types, not BaseDevice
        ),
        "security_level" / Int8ub,
        "flags" / Padded(1, Optional(BitStruct(
            Padding(8)
        ))),
        "private_key_len" / Int16ub,
        "private_key" / Bytes(this.private_key_len),
        "client_id_len" / Int16ub,
        "client_id" / Bytes(this.client_id_len)
    )
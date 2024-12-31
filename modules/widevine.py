from construct import Struct, Const, Int8ub, Bytes, Int32ub, Int16ub, Optional, Padded, Flag, BitStruct, Padding, If, this
from construct import Enum as CEnum
from enum import IntEnum
import construct

# Check Construct Version
CONSTRUCT_VERSION = tuple(map(int, construct.__version__.split('.')))


class BaseDevice:
    class Types(IntEnum):
        CHROME = 1
        ANDROID = 2


class WidevineDeviceStruct(BaseDevice):
    magic = Const(b"WVD")

    # Helper to handle Const differences between versions
    def version_const(value):
        if CONSTRUCT_VERSION >= (2, 10, 67):
            return Const(value, Int8ub)  # Newer syntax
        else:
            return Const(Int8ub, value)  # Older syntax

    header = Struct(
        "signature" / magic,
        "version" / Int8ub
    )

    WidevineDeviceStructVersion_1 = Struct(
        "signature" / magic,
        "version" / version_const(1),  # Dynamic Const based on version
        "type_" / CEnum(
            Int8ub,
            **{t.name: t.value for t in BaseDevice.Types}
        ),
        "security_level" / Int8ub,
        "flags" / Padded(1, Optional(BitStruct(
            Padding(8)
        ))),
        "private_key_len" / Int16ub,
        "private_key" / Bytes(this.private_key_len),
        "client_id_len" / Int16ub,
        "client_id" / Bytes(this.client_id_len),
        "vmp_len" / Int16ub,
        "vmp" / Bytes(this.vmp_len)
    )

    WidevineDeviceStructVersion_2 = Struct(
        "signature" / magic,
        "version" / version_const(2),  # Dynamic Const based on version
        "type_" / CEnum(
            Int8ub,
            **{t.name: t.value for t in BaseDevice.Types}
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
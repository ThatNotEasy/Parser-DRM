from construct import Struct, Const, Int8ub, Bytes, Int32ub, Int16ub, Optional, Padded, Flag, BitStruct, Padding, If, this
from construct import Enum as CEnum
from enum import IntEnum
import construct
import struct
import base64
from zlib import crc32
from Crypto.Cipher import AES

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
    
    
class KeyboxStruct:
    Keybox = Struct(
        "stable_id" / Bytes(32),
        "device_aes_key" / Bytes(16),
        "device_id" / Bytes(72),
        "body_crc" / Int32ub,
        "magic" / Bytes(4)  # Remove `Const` constraint to allow flexibility
    )
    
    


def parse_keybox(file_path):
    try:
        # Read the binary file
        with open(file_path, "rb") as f:
            keybox_data = f.read()

        # Ensure the file length is as expected
        if len(keybox_data) != 128:
            raise ValueError(f"Unexpected keybox length: {len(keybox_data)} bytes. Expected 128 bytes.")

        # Define offsets for the fields
        keybox_format = {
            "stable_id": (0, 32),         # Bytes 0-31
            "device_aes_key": (32, 48),   # Bytes 32-47
            "device_id": (48, 120),       # Bytes 48-119
            "body_crc": (120, 124),       # Bytes 120-123
            "magic": (124, 128)           # Bytes 124-127
        }

        # Extract the fields
        parsed_keybox = {
            "Stable ID": keybox_data[keybox_format["stable_id"][0]:keybox_format["stable_id"][1]].hex(),
            "Device AES Key": keybox_data[keybox_format["device_aes_key"][0]:keybox_format["device_aes_key"][1]].hex(),
            "Device ID": keybox_data[keybox_format["device_id"][0]:keybox_format["device_id"][1]].hex(),
            "Body CRC": f"0x{struct.unpack('>I', keybox_data[keybox_format['body_crc'][0]:keybox_format['body_crc'][1]])[0]:08X}",
            "Magic": keybox_data[keybox_format["magic"][0]:keybox_format["magic"][1]].hex()
        }

        # Convert to Base64
        base64_keybox = {
            "Stable ID": base64.b64encode(bytes.fromhex(parsed_keybox["Stable ID"])).decode("utf-8"),
            "Device AES Key": base64.b64encode(bytes.fromhex(parsed_keybox["Device AES Key"])).decode("utf-8"),
            "Device ID": base64.b64encode(bytes.fromhex(parsed_keybox["Device ID"])).decode("utf-8")
        }

        # Analyze Device ID
        device_id = bytes.fromhex(parsed_keybox["Device ID"])
        device_id_analysis = {
            "Flags": device_id[:4].hex(),
            "Metadata": device_id[4:].hex()
        }

        # Recompute CRC
        computed_crc = crc32(keybox_data[:120]) & 0xFFFFFFFF
        crc_valid = computed_crc == struct.unpack('>I', keybox_data[keybox_format['body_crc'][0]:keybox_format['body_crc'][1]])[0]

        # Test CRC with additional scope (including magic)
        computed_crc_with_magic = crc32(keybox_data[:124]) & 0xFFFFFFFF

        # Attempt to decrypt Metadata using Device AES Key
        aes_key = bytes.fromhex(parsed_keybox["Device AES Key"])
        metadata = device_id[4:]
        try:
            # Add padding to make the metadata length a multiple of 16 bytes
            padded_metadata = metadata + b"\x00" * (16 - len(metadata) % 16)
            cipher = AES.new(aes_key, AES.MODE_ECB)
            decrypted_metadata = cipher.decrypt(padded_metadata)
            decrypted_metadata_hex = decrypted_metadata[:len(metadata)].hex()  # Trim padding

            # Analyze decrypted metadata for potential fields
            metadata_analysis = {
                "Decrypted Hex": decrypted_metadata_hex,
                "Decrypted ASCII": ''.join(chr(b) if 32 <= b <= 126 else '.' for b in decrypted_metadata[:len(metadata)])
            }

        except Exception as e:
            decrypted_metadata_hex = f"Decryption failed: {e}"
            metadata_analysis = {}

        return parsed_keybox, base64_keybox, device_id_analysis, crc_valid, computed_crc_with_magic, decrypted_metadata_hex, metadata_analysis

    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error parsing keybox: {e}")
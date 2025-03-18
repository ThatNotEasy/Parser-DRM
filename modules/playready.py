import base64
import binascii
import re
import logging
from typing import Union
from construct import Struct, Int8ub, Int32ub, Bytes, this, Container, ConstructError
from enum import IntEnum
import construct

CONSTRUCT_VERSION = tuple(map(int, construct.__version__.split('.')))
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class BaseDevice:
    class Types(IntEnum):
        EDGE = 1
        ANDROID = 2

class PlayReadyDeviceStruct(BaseDevice):
    EXPECTED_SIGNATURES = [b"PRD", b"PRK"]

    PlayReadyDeviceStructVersion_1 = Struct(
        "signature" / Bytes(3),
        "version" / Int8ub,
        "group_key_length" / Int32ub,
        "group_key" / Bytes(this.group_key_length),
        "group_certificate_length" / Int32ub,
        "group_certificate" / Bytes(this.group_certificate_length),
    )

    PlayReadyDeviceStructVersion_2 = Struct(
        "signature" / Bytes(3),
        "version" / Int8ub,
        "group_certificate_length" / Int32ub,
        "group_certificate" / Bytes(this.group_certificate_length),
        "encryption_key" / Bytes(96),
        "signing_key" / Bytes(96),
    )

    PlayReadyDeviceStructVersion_3 = Struct(
        "signature" / Bytes(3),
        "version" / Int8ub,
        "group_key" / Bytes(96),
        "encryption_key" / Bytes(96),
        "signing_key" / Bytes(96),
        "group_certificate_length" / Int32ub,
        "group_certificate" / Bytes(this.group_certificate_length),
    )
    
    @staticmethod
    def read_hex(file_path):
        sl2k_offset = 0x000007D0  # PlayReady SL2000 Device + Link Root CA
        sl3k_offset = 0x00000773  # PlayReady SL3000 Device Port + Link CA
        device_offsets = [0x0000028C, 0x00000298, 0x000002A4]  # Offsets for Device Name
        
        try:
            with open(file_path, "rb") as file:
                data = file.read()

            security_level = "Unknown"
            if sl2k_offset < len(data) and data[sl2k_offset:sl2k_offset+30].find(b"SL2000") != -1:
                security_level = "SL2000"
            elif sl3k_offset < len(data) and data[sl3k_offset:sl3k_offset+30].find(b"SL3000") != -1:
                security_level = "SL3000"

            device_parts = []
            for offset in device_offsets:
                if offset < len(data):
                    string_part = data[offset:offset+20].split(b'\x00', 1)[0].decode("utf-8", errors="ignore")
                    device_parts.append(string_part)

            full_name = " ".join(filter(None, device_parts)).strip()
            if not full_name:
                full_name = "Unknown Device"

            return {"device_name": full_name, "security_level": security_level}
        
        except FileNotFoundError:
            logging.error(f"Error: File '{file_path}' not found.")
            return None
        except Exception as e:
            logging.error(f"Error reading file: {e}")
            return None

    @staticmethod
    def parse_playready_device(data: bytes):
        for version, struct in [
            (3, PlayReadyDeviceStruct.PlayReadyDeviceStructVersion_3),
            (2, PlayReadyDeviceStruct.PlayReadyDeviceStructVersion_2),
            (1, PlayReadyDeviceStruct.PlayReadyDeviceStructVersion_1),
        ]:
            try:
                logging.debug(f"Attempting to parse using PlayReadyDeviceStructVersion_{version}")
                parsed_data = struct.parse(data)
                if parsed_data.signature not in PlayReadyDeviceStruct.EXPECTED_SIGNATURES:
                    raise ValueError(
                        f"Unexpected signature: {parsed_data.signature}. Expected one of {PlayReadyDeviceStruct.EXPECTED_SIGNATURES}"
                    )
                if parsed_data.version != version:
                    raise ValueError(
                        f"Unexpected version: {parsed_data.version}. Expected {version}"
                    )
                return parsed_data
            except ConstructError as e:
                logging.warning(f"Failed to parse with Version_{version}: {e}")
            except ValueError as e:
                logging.warning(f"Validation failed for Version_{version}: {e}")
        raise ValueError("Unable to parse PlayReady device data using available structures.")
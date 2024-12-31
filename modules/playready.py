import base64
import logging
from typing import Union
from construct import Struct, Int8ub, Int32ub, Bytes, this, Container, ConstructError
from enum import IntEnum
import construct

# Check Construct Version
CONSTRUCT_VERSION = tuple(map(int, construct.__version__.split('.')))


class BaseDevice:
    class Types(IntEnum):
        EDGE = 1
        ANDROID = 2


class PlayReadyDeviceStruct(BaseDevice):
    # Expected signatures
    EXPECTED_SIGNATURES = [b"PRD", b"PRK"]

    # Device structure for different versions
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

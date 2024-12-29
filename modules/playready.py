import base64
import logging
from typing import Union
from construct import Struct, Const, Int8ub, Int32ub, Bytes, this, Container, ConstructError
from enum import IntEnum


class BaseDevice:
    class Types(IntEnum):
        EDGE = 1
        ANDROID = 2


class PlayReadyDeviceStruct(BaseDevice):
    magic = Const(b"PRD")
    header = Struct(
        "signature" / magic,
        "version" / Int8ub,
    )

    PlayReadyDeviceStructVersion_1 = Struct(
        "signature" / magic,
        "version" / Int8ub,
        "group_key_length" / Int32ub,
        "group_key" / Bytes(this.group_key_length),
        "group_certificate_length" / Int32ub,
        "group_certificate" / Bytes(this.group_certificate_length),
    )

    PlayReadyDeviceStructVersion_2 = Struct(
        "signature" / magic,
        "version" / Int8ub,
        "group_certificate_length" / Int32ub,
        "group_certificate" / Bytes(this.group_certificate_length),
        "encryption_key" / Bytes(96),
        "signing_key" / Bytes(96),
    )

    PlayReadyDeviceStructVersion_3 = Struct(
        "signature" / magic,
        "version" / Int8ub,
        "group_key" / Bytes(96),
        "encryption_key" / Bytes(96),
        "signing_key" / Bytes(96),
        "group_certificate_length" / Int32ub,
        "group_certificate" / Bytes(this.group_certificate_length),
    )

    @staticmethod
    def parse_playready_device(data: bytes):
        try:
            logging.debug("Attempting to parse using PlayReadyDeviceStructVersion_3")
            return PlayReadyDeviceStruct.PlayReadyDeviceStructVersion_3.parse(data)
        except ConstructError as e:
            logging.warning(f"Failed to parse with Version_3: {e}")
            try:
                logging.debug("Falling back to PlayReadyDeviceStructVersion_2")
                return PlayReadyDeviceStruct.PlayReadyDeviceStructVersion_2.parse(data)
            except ConstructError as e2:
                logging.error(f"Failed to parse with Version_2: {e2}")
                raise ValueError("Unable to parse PlayReady device data using available structures.")

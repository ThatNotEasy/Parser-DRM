from construct import Struct, Bytes, Int32ub
from colorama import Fore, Style
from zlib import crc32
from Crypto.Cipher import AES
import struct, base64, requests, time, os
import xml.etree.ElementTree as ET
from modules.logger import setup_logging
from cryptography import x509

logging = setup_logging()

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
            raise ValueError(f"{Fore.RED}Unexpected keybox length: {len(keybox_data)} bytes. Expected 128 bytes.{Style.RESET_ALL}")

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
            decrypted_metadata_hex = f"{Fore.RED}Decryption failed: {e}{Style.RESET_ALL}"
            metadata_analysis = {}

        return parsed_keybox, base64_keybox, device_id_analysis, crc_valid, computed_crc_with_magic, decrypted_metadata_hex, metadata_analysis

    except FileNotFoundError:
        raise FileNotFoundError(f"{Fore.RED}File not found: {file_path}{Style.RESET_ALL}")
    except Exception as e:
        raise RuntimeError(f"{Fore.RED}Error parsing keybox: {e}{Style.RESET_ALL}")
    
    
def check_keybox_revocation():
    api = f'https://android.googleapis.com/attestation/status?{time.time_ns()}'
    try:
        crl = requests.get(api, headers={'Cache-Control': 'max-age=0'}).json()
        return crl
    except Exception:
        return {"entries": {}}

def parse_cert(cert):
    try:
        cert = "\n".join(line.strip() for line in cert.strip().split("\n"))
        parsed = x509.load_pem_x509_certificate(cert.encode())
        serial = f'{parsed.serial_number:x}'
        return serial
    except Exception:
        return None

def check(xml_file):
    try:
        certs = [elem.text for elem in ET.parse(xml_file).getroot().iter() if elem.tag == 'Certificate']

        if len(certs) < 4:
            return {"Status": "Invalid XML"}

        ec_cert_sn = parse_cert(certs[0])
        rsa_cert_sn = parse_cert(certs[3])

        if not ec_cert_sn or not rsa_cert_sn:
            return {"Status": "Missing Serial"}

        crl = check_keybox_revocation()
        is_revoked = any(sn in crl.get("entries", {}) for sn in (ec_cert_sn, rsa_cert_sn))

        return {
            "EC Cert SN": ec_cert_sn,
            "RSA Cert SN": rsa_cert_sn,
            "Revoked Status": "Revoked" if is_revoked else "Valid"
        }

    except ET.ParseError:
        return {"Status": "Malformed XML"}
    except Exception:
        return {"Status": "Processing Error"}

def keybox_main(path):
    if os.path.isfile(path) and path.endswith(".xml"):
        return check(path)
    else:
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.xml'):
                    xml_file = os.path.join(root, file)
                    return check(xml_file)
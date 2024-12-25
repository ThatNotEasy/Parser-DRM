import base64

def convert_bytes_to_base64(byte_data):
    return base64.b64encode(byte_data).decode("utf-8")
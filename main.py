import os
from colorama import init, Fore, Style
from modules.logger import setup_logging
from modules.banners import banners, clear_terminal
from modules.utils import convert_bytes_to_base64
from modules.keybox import parse_keybox, keybox_main
from modules.widevine import WidevineDeviceStruct
from modules.playready import PlayReadyDeviceStruct

init(autoreset=True)
logging = setup_logging()

def read_device_file(file_path):
    """Reads and parses a DRM device file (PlayReady or Widevine)."""
    file_extension = os.path.splitext(file_path)[1].lower()
    parsed_data, device_type = None, None

    if file_extension in [".prd", ".dat", ".bin"]:
        device_type = "PlayReady"
        structs = [
            ("Version 3", PlayReadyDeviceStruct.PlayReadyDeviceStructVersion_3),
            ("Version 2", PlayReadyDeviceStruct.PlayReadyDeviceStructVersion_2),
            ("Version 1", PlayReadyDeviceStruct.PlayReadyDeviceStructVersion_1),
        ]

        try:
            hex_result = PlayReadyDeviceStruct.read_hex(file_path)
            device_name = hex_result.get("device_name", "Unknown Device") if hex_result else "Unknown Device"
            security_level = hex_result.get("security_level", "Unknown Security Level") if hex_result else "Unknown Security Level"
        except Exception as e:
            logging.warning(f"read_hex() failed: {e}. Using default values.")
            device_name, security_level = "Unknown Device", "Unknown Security Level"

        try:
            with open(file_path, "rb") as file:
                file_data = file.read()

            for version_name, struct in structs:
                try:
                    parsed_data = struct.parse(file_data)
                    parsed_data["device_name"] = device_name
                    parsed_data["security_level"] = security_level

                    return parsed_data, device_type
                except Exception as e:
                    logging.warning(f"Error parsing PlayReady file with {version_name}: {e}")

        except Exception as e:
            logging.error(f"Failed to read file: {e}")

    elif file_extension == ".wvd":
        device_type = "Widevine"
        structs = [
            ("Version 2", WidevineDeviceStruct.WidevineDeviceStructVersion_2),
            ("Version 1", WidevineDeviceStruct.WidevineDeviceStructVersion_1),
        ]

        try:
            with open(file_path, "rb") as file:
                file_data = file.read()

            for version_name, struct in structs:
                try:
                    parsed_data = struct.parse(file_data)
                    return parsed_data, device_type
                except Exception as e:
                    logging.warning(f"Error parsing Widevine file with {version_name}: {e}")

        except Exception as e:
            logging.error(f"Failed to read file: {e}")

    elif file_extension in [".enc", ".keybox", ".bin"]:
        device_type = "Widevine Keybox"
        try:
            parsed_keybox, base64_keybox, device_id_analysis, crc_valid, crc_with_magic, decrypted_metadata, metadata_analysis = parse_keybox(file_path)

            return {
                "parsed_keybox": parsed_keybox,
                "base64_keybox": base64_keybox,
                "device_id_analysis": device_id_analysis,
                "crc_valid": crc_valid,
                "crc_with_magic": crc_with_magic,
                "decrypted_metadata": decrypted_metadata,
                "metadata_analysis": metadata_analysis
            }, device_type
        except Exception as e:
            logging.error(f"Error parsing Widevine Keybox file: {e}")
            return None, device_type
        
    elif ".xml" in file_extension:
        device_type = "Widevine Keybox XML"
        try:
            result = keybox_main(file_path)
            return result, device_type
        except Exception as e:
            logging.error(f"Error processing Widevine Keybox XML file: {e}")
            return {"Status": "Error"}, device_type

def process_directory(directory_path):
    """Finds all devices in the specified directory."""
    devices = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            devices.append((filename, file_path))
    return devices

def choose_device(devices):
    """Displays available devices with a structured UI and allows user selection."""
    if not devices:
        print(f"\n{Fore.RED}No devices found to process.{Style.RESET_ALL}")
        exit(1)

    box_width = 64  # Ensures consistent width
    title = " Available Device Files "
    title_bar = f"╔{'═' * (box_width - 2)}╗"
    title_text = f"║{title.center(box_width - 2)}║"
    separator = f"╠{'═' * (box_width - 2)}╣"
    bottom_border = f"╚{'═' * (box_width - 2)}╝"

    print(f"\n{Fore.CYAN}{title_bar}{Fore.RESET}")
    print(f"{title_text}")
    print(f"{separator}")

    for idx, (filename, _) in enumerate(devices, 1):
        file_display = filename[:50] + "..." if len(filename) > 50 else filename
        print(f"║ {Fore.YELLOW}{idx:<2} . {Fore.GREEN}{file_display:<55}{Fore.CYAN} ║{Fore.RESET}")

    print(bottom_border + Style.RESET_ALL)

    while True:
        try:
            choice = int(input(f"\n{Fore.CYAN}Enter the number of the device you want to view (1-{len(devices)}): {Style.RESET_ALL}"))
            if 1 <= choice <= len(devices):
                return devices[choice - 1]
            else:
                print(f"{Fore.RED}Invalid choice. Please enter a number between 1 and {len(devices)}.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter a valid number.{Style.RESET_ALL}")

def pretty_print(data, device_type):
    """Prints parsed data in a structured format."""
    if not data:
        print(f"{Fore.RED}Failed to parse {device_type} file.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}╔════════════════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}                      {Fore.YELLOW}Parsed {device_type} Data                  {Fore.CYAN} {Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")

    for field, value in data.items():
        if isinstance(value, bytes):
            value = convert_bytes_to_base64(value)
        elif isinstance(value, int):
            value = f"{value:,}"
        elif isinstance(value, bool):
            value = f"{Fore.GREEN}Enabled{Style.RESET_ALL}" if value else f"{Fore.RED}Disabled{Style.RESET_ALL}"
        elif value is None:
            value = f"{Fore.YELLOW}N/A{Style.RESET_ALL}"

        print(f"{Fore.MAGENTA}{field.replace('_', ' ').title():<30}:{Style.RESET_ALL} {Fore.WHITE}{value}{Style.RESET_ALL}")

    print(Fore.CYAN + "═" * 70 + Style.RESET_ALL + "\n")

def main():
    """Automatically displays available devices and allows user to choose which one to parse."""
    clear_terminal()
    banners()
    devices_directory = "devices"

    if not os.path.isdir(devices_directory):
        print(f"{Fore.RED}Directory 'devices' does not exist. Exiting...{Style.RESET_ALL}")
        exit(1)

    devices = process_directory(devices_directory)

    if not devices:
        print(f"{Fore.RED}No devices found to process.{Style.RESET_ALL}")
        exit(1)

    selected_device = choose_device(devices)
    filename, file_path = selected_device
    clear_terminal()
    banners()
    print(f"{Fore.CYAN}Processing file: {filename}{Style.RESET_ALL}")

    parsed_data, device_type = read_device_file(file_path)
    pretty_print(parsed_data, device_type)

if __name__ == "__main__":
    main()

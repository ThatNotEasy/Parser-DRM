from modules.playready import PlayReadyDeviceStruct
from modules.widevine import WidevineDeviceStruct
from colorama import init, Fore, Style
from modules.banners import banners, clear_terminal
from modules.utils import convert_bytes_to_base64
import os

init(autoreset=True)

def read_device_file(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension == ".prd":
        device_type = "PlayReady"
        struct = PlayReadyDeviceStruct.PlayReadyDeviceStructVersion
    elif file_extension == ".wvd":
        device_type = "Widevine"
        struct = WidevineDeviceStruct.WidevineDeviceStructVersion
    else:
        print(f"{Fore.RED}Unsupported file type: {file_extension}. Only .prd and .wvd are supported.{Style.RESET_ALL}")
        return None

    with open(file_path, "rb") as file:
        file_data = file.read()

    try:
        parsed_data = struct.parse(file_data)
        return parsed_data, device_type
    except Exception as e:
        print(f"{Fore.RED}Error while parsing {device_type} file: {e}{Style.RESET_ALL}")
        return None

def pretty_print(data, device_type):
    if data:
        print(f"\n{Fore.CYAN}--- Parsed {device_type} Data ---{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 30}{Style.RESET_ALL}")
        for field, value in data.items():
            if isinstance(value, bytes):
                value = convert_bytes_to_base64(value)
            elif isinstance(value, int):
                value = f"{value:,}"
            elif isinstance(value, bool):
                value = f"{Fore.GREEN}Enabled{Style.RESET_ALL}" if value else f"{Fore.RED}Disabled{Style.RESET_ALL}"
            elif value is None:
                value = f"{Fore.YELLOW}N/A{Style.RESET_ALL}"
            
            print(f"{Fore.MAGENTA}{field.replace('_', ' ').title():<30}: {Fore.WHITE}{value}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 30}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to parse {device_type} file.{Style.RESET_ALL}")

def process_directory(directory_path):
    # Loop through all files in the directory
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        
        # Only process .prd and .wvd files
        if os.path.isfile(file_path) and (filename.endswith(".prd") or filename.endswith(".wvd")):
            print(f"\n{Fore.CYAN}Processing file: {filename}{Style.RESET_ALL}")
            parsed_data, device_type = read_device_file(file_path)
            pretty_print(parsed_data, device_type)

def main():
    devices_directory = "devices"  # Assuming the devices directory is at the current level
    
    if not os.path.isdir(devices_directory):
        print(f"{Fore.RED}Directory 'devices' does not exist. Exiting...{Style.RESET_ALL}")
        return

    process_directory(devices_directory)

if __name__ == "__main__":
    clear_terminal()
    banners()
    main()

from colorama import init, Fore, Style
from modules.banners import banners, clear_terminal
from modules.utils import convert_bytes_to_base64
from modules.widevine import WidevineDeviceStruct
from modules.playready import PlayReadyDeviceStruct
import os

init(autoreset=True)

def read_device_file(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".prd":
        device_type = "PlayReady"
        struct = PlayReadyDeviceStruct.PlayReadyDeviceStructVersion_3
    elif file_extension == ".wvd":
        device_type = "Widevine"
        struct = WidevineDeviceStruct.WidevineDeviceStructVersion_2
    else:
        device_type = "Unknown"
        struct = None

    with open(file_path, "rb") as file:
        file_data = file.read()

    try:
        if struct:
            try:
                parsed_data = struct.parse(file_data)
                return parsed_data, device_type
            except Exception as e:
                print(f"{Fore.RED}Error parsing {device_type} file with version 1: {e}{Style.RESET_ALL}")
                if device_type == "Widevine":
                    print(f"{Fore.YELLOW}Attempting with WidevineDeviceStructVersion_2...{Style.RESET_ALL}")
                    try:
                        struct = WidevineDeviceStruct.WidevineDeviceStructVersion_1
                        parsed_data = struct.parse(file_data)
                        return parsed_data, device_type
                    except Exception as e2:
                        print(f"{Fore.RED}Error parsing Widevine file with version 1: {e2}{Style.RESET_ALL}")
                elif device_type == "PlayReady":
                    print(f"{Fore.YELLOW}\nAttempting with PlayReadyDeviceStructVersion_3...{Style.RESET_ALL}")
                    try:
                        struct = PlayReadyDeviceStruct.PlayReadyDeviceStructVersion_3
                        parsed_data = struct.parse(file_data)
                        return parsed_data, device_type
                    except Exception as e3:
                        print(f"{Fore.RED}Error parsing PlayReady file with version 3: {e3}{Style.RESET_ALL}")
                        try:
                            struct = PlayReadyDeviceStruct.PlayReadyDeviceStructVersion_2
                            parsed_data = struct.parse(file_data)
                            return parsed_data, device_type
                        except Exception as e4:
                            print(f"{Fore.RED}Error parsing PlayReady file with version 2: {e3}{Style.RESET_ALL}")
                    
        else:
            print(f"{Fore.YELLOW}Skipping {file_path}, Unsupported Device Type{Style.RESET_ALL}")
            return None, device_type
    except Exception as e:
        print(f"{Fore.RED}Error while parsing {device_type} file: {e}{Style.RESET_ALL}")
        return None, device_type

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
    devices = []
    
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        
        if os.path.isfile(file_path):
            devices.append((filename, file_path))
    
    return devices

def choose_device(devices):
    if not devices:
        print(f"{Fore.RED}No devices found to process.{Style.RESET_ALL}")
        return None

    print(f"\n{Fore.CYAN}Available Devices:{Style.RESET_ALL}")
    print(Fore.WHITE + ".++" + "=" * 50 + "++.\n" + Style.RESET_ALL)
    for idx, (filename, _) in enumerate(devices, 1):
        print(f"{Fore.MAGENTA}{idx}. {filename}{Style.RESET_ALL}")

    try:
        choice = int(input(f"\n{Fore.CYAN}Enter the number of the device you want to view (1-{len(devices)}): {Style.RESET_ALL}"))
        if 1 <= choice <= len(devices):
            return devices[choice - 1]
        else:
            print(f"{Fore.RED}Invalid choice. Exiting...{Style.RESET_ALL}")
            return None
    except ValueError:
        print(f"{Fore.RED}Invalid input. Please enter a number.{Style.RESET_ALL}")
        return None

def main():
    devices_directory = "devices"
    
    if not os.path.isdir(devices_directory):
        print(f"{Fore.RED}Directory 'devices' does not exist. Exiting...{Style.RESET_ALL}")
        return

    devices = process_directory(devices_directory)

    selected_device = choose_device(devices)
    if selected_device:
        filename, file_path = selected_device
        banners()
        print(f"\n{Fore.CYAN}Processing file: {filename}{Style.RESET_ALL}")
        parsed_data, device_type = read_device_file(file_path)
        pretty_print(parsed_data, device_type)

if __name__ == "__main__":
    banners()
    main()

import os
import subprocess
from colorama import init, Fore, Style
from modules.banners import banners, clear_terminal
from modules.utils import convert_bytes_to_base64
from modules.widevine import WidevineDeviceStruct, KeyboxStruct
from modules.playready import PlayReadyDeviceStruct

init(autoreset=True)

def run_command(command, description="executing the command"):
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}Error: Failed to {description}{Style.RESET_ALL}")
        exit(1)

def reinstall_libraries():
    clear_terminal()
    banners()
    run_command("pip uninstall -y pywidevine pyplayready construct pymp4", "uninstall libraries")
    run_command("pip install pywidevine pyplayready construct pymp4", "install libraries")
    print(f"🌐  {Fore.GREEN}Libraries reinstalled successfully!{Style.RESET_ALL}")

def run_migrate_device():
    clear_terminal()
    banners()
    
    exe_path = os.path.join("modules", "migrate_device.exe")
    
    if not os.path.isfile(exe_path):
        print(f"{Fore.RED}Error: 'migrate_device.exe' not found in 'modules' directory.{Style.RESET_ALL}")
        exit(1)

    print(f"{Fore.GREEN}Running migrate_device.exe...{Style.RESET_ALL}\n")
    exit_code = os.system(f'"{exe_path}"')
    if exit_code == 0:
        print(f"{Fore.GREEN}Migration completed successfully!{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Error: Failed to execute migrate-device.exe. Exit code: {exit_code}{Style.RESET_ALL}")
    exit(exit_code)

def read_device_file(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()
    parsed_data, device_type = None, None

    if file_extension in [".prd", ".dat"]:
        device_type = "PlayReady"
        structs = [
            PlayReadyDeviceStruct.PlayReadyDeviceStructVersion_3,
            PlayReadyDeviceStruct.PlayReadyDeviceStructVersion_2,
            PlayReadyDeviceStruct.PlayReadyDeviceStructVersion_1,
        ]
    elif file_extension == ".wvd":
        device_type = "Widevine"
        structs = [
            WidevineDeviceStruct.WidevineDeviceStructVersion_2,
            WidevineDeviceStruct.WidevineDeviceStructVersion_1,
        ]
    elif file_extension == ".enc":
        device_type = "Widevine Keybox"
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
            parsed_data = KeyboxStruct.Keybox.parse(file_data)
            return parsed_data, device_type
        except Exception as e:
            print(f"{Fore.RED}Error parsing Widevine Keybox file: {e}{Style.RESET_ALL}")
            return None, device_type
    else:
        print(f"{Fore.YELLOW}Unsupported file type: {file_extension}{Style.RESET_ALL}")
        return None, None

    if structs:
        with open(file_path, "rb") as file:
            file_data = file.read()

        for idx, struct in enumerate(structs, start=1):
            try:
                parsed_data = struct.parse(file_data)
                return parsed_data, device_type
            except Exception as e:
                print(f"{Fore.RED}Error parsing {device_type} file with version {idx}: {e}{Style.RESET_ALL}")

    print(f"{Fore.RED}Failed to parse {device_type} file with all available versions.{Style.RESET_ALL}")
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
        exit(1)

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
            exit(1)
    except ValueError:
        print(f"{Fore.RED}Invalid input. Please enter a number.{Style.RESET_ALL}")
        exit(1)

def parser_drm_device():
    clear_terminal()
    banners()
    devices_directory = "devices"
    if not os.path.isdir(devices_directory):
        print(f"{Fore.RED}Directory 'devices' does not exist. Exiting...{Style.RESET_ALL}")
        exit(1)

    devices = process_directory(devices_directory)
    selected_device = choose_device(devices)
    if selected_device:
        filename, file_path = selected_device
        clear_terminal()
        banners()
        print(f"\n{Fore.CYAN}Processing file: {filename}{Style.RESET_ALL}")
        parsed_data, device_type = read_device_file(file_path)
        pretty_print(parsed_data, device_type)
        exit(0)

def main_menu():
    reinstall_libraries()
    while True:
        clear_terminal()
        banners()
        print(f"{Fore.GREEN}Please select an option:{Style.RESET_ALL}\n")
        print(f"{Fore.YELLOW}[1] {Fore.RED}- {Fore.GREEN}Parse DRM Device{Fore.RESET}")
        print(f"{Fore.YELLOW}[2] {Fore.RED}- {Fore.GREEN}Migrate/Upgrade Device{Fore.RESET}")
        print(f"{Fore.YELLOW}[3] {Fore.RED}- {Fore.GREEN}Exit{Fore.RESET}")

        choice = input(f"\n{Fore.CYAN}Enter your choice: {Style.RESET_ALL}")
        if choice == "1":
            parser_drm_device()
        elif choice == "2":
            run_migrate_device()
        elif choice == "3":
            print(f"{Fore.GREEN}Exiting...{Style.RESET_ALL}")
            exit(0)
        else:
            print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")

if __name__ == "__main__":
    clear_terminal()
    banners()
    print(f"🌐  {Fore.RED}Reinstalling required packages for compatibility ...{Fore.RESET}")
    run_command("pip uninstall -y pywidevine pyplayready construct pymp4", "uninstall libraries")
    run_command("pip install pywidevine pyplayready construct pymp4", "install libraries")
    main_menu()
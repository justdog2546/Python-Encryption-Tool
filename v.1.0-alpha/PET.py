# python 3.15.1
# Python Encryption Tool (PET) v1.0-alpha
# Made by : justdog2546
# support by Github copilot (thank AI!)

#loading modules
print("Python Encryption Tool (PET) v1.0-alpha")
print("loading modules...")

import importlib
import os
import platform
import secrets
import string
import struct
import subprocess
import sys
import time

module_errors = []


def load_module(module_name):
    try:
        globals()[module_name] = importlib.import_module(module_name)
        return True
    except ImportError as error:
        module_errors.append(f"{module_name}: {error}")
        print(f"Failed to load module: {module_name}")
        return False


def load_os_modules():
    current_os = platform.system()

    if current_os == "Windows":
        print("OS Detected : Windows")
        runtime_modules = ["winreg", "ctypes"]
        loaded = [name for name in runtime_modules if load_module(name)]
        if loaded:
            print(f"Loaded OS-specific modules: {', '.join(loaded)}")
    elif current_os == "Linux":
        print("OS Detected : Linux")
        runtime_modules = ["grp", "pwd", "os"]
        loaded = [name for name in runtime_modules if load_module(name)]
        if loaded:
            print(f"Loaded OS-specific modules: {', '.join(loaded)}")
    elif current_os == "Darwin":
        print("OS Detected : macOS")
        runtime_modules = ["pwd", "os"]
        loaded = [name for name in runtime_modules if load_module(name)]
        if loaded:
            print(f"Loaded OS-specific modules: {', '.join(loaded)}")
    else:
        print("No OS-specific modules are configured for this operating system.")
        print("FAIL : OS Detection Error Manual load modules required")
        chosen_os = input("Pleas Select Your OS [1.Windows 2.Gnu/Linux 3.macOS] (Input Number) : ")
        if chosen_os == "1":
            if load_module("winreg"):
                print("Loaded OS-specific module: winreg")
        elif chosen_os in {"2", "3"}:
            if load_module("pwd"):
                print("Loaded OS-specific module: pwd")
        else:
            print("E : Invalid input. Fail to Load Modules.")


load_os_modules()
print("Completed load modules.")
print("Checking Modules Errors...")
if module_errors:
    print("Module loading errors detected:")
    for error in module_errors:
        print(f"- {error}")
else:
    print("No module loading errors detected.")


def ensure_cryptography():
    try:
        from cryptography.exceptions import InvalidTag
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return True, InvalidTag, AESGCM
    except ImportError:
        pass

    if os.environ.get("PET_BOOTSTRAPPED") == "1":
        print("cryptography could not be imported even after installation.")
        raise SystemExit(1)

    print("cryptography is missing. install to this commands : python -m pip install cryptography")
    exit()


    active_virtualenv = sys.prefix != sys.base_prefix
    if active_virtualenv:
        install_result = install_with(sys.executable)
        if install_result.returncode == 0:
            from cryptography.exceptions import InvalidTag
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            return True, InvalidTag, AESGCM
        print("Installation in the active virtual environment failed.")
        print((install_result.stderr or install_result.stdout).strip())

    if os.name == "nt":
        data_dir = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    else:
        data_dir = os.environ.get(
            "XDG_DATA_HOME",
            os.path.join(os.path.expanduser("~"), ".local", "share"),
        )
    venv_dir = os.path.join(data_dir, "PET", "venv")
    venv_python = (
        os.path.join(venv_dir, "Scripts", "python.exe")
        if os.name == "nt"
        else os.path.join(venv_dir, "bin", "python")
    )

    if not os.path.isfile(venv_python):
        create_result = subprocess.run(
            [sys.executable, "-m", "venv", venv_dir],
            capture_output=True,
            text=True,
        )
        if create_result.returncode != 0:
            print("Could not create PET's isolated virtual environment.")
            print((create_result.stderr or create_result.stdout).strip())
            raise SystemExit(1)

    install_result = install_with(venv_python)
    if install_result.returncode != 0:
        print("Automatic installation failed in PET's isolated environment.")
        print((install_result.stderr or install_result.stdout).strip())
        raise SystemExit(1)

    env = os.environ.copy()
    env["PET_BOOTSTRAPPED"] = "1"
    os.execve(venv_python, [venv_python, os.path.abspath(__file__), *sys.argv[1:]], env)


CRYPT_OK, InvalidTag, AESGCM = ensure_cryptography()

os.system("cls" if os.name == "nt" else "clear")

#start of the program
print(
    """###          #    #                       ####                                 #     #                      ###               ##    
#  #         #    #                       #                                    #                             #                 #    
#  #  #  #  ###   ###    ##   ###         ###   ###    ##   ###   #  #  ###   ###   ##     ##   ###          #     ##    ##    #    
###   #  #   #    #  #  #  #  #  #        #     #  #  #     #  #  #  #  #  #   #     #    #  #  #  #         #    #  #  #  #   #    
#      # #   #    #  #  #  #  #  #        #     #  #  #     #      # #  #  #   #     #    #  #  #  #         #    #  #  #  #   #    
#       #     ##  #  #   ##   #  #        ####  #  #   ##   #       #   ###     ##  ###    ##   #  #         #     ##    ##   ###   
       #                                                           #    #                                                           """
)
print("Made by : justdog2546")

FILE_MAGIC = b"PET1"
NONCE_LENGTH = 12
KEY_LENGTH = 16
KEY_CHARACTERS = string.ascii_letters + string.digits


def get_key_file_path(user_path):
    user_path = user_path.strip().strip('"')
    if not user_path:
        raise ValueError("The key file path cannot be empty.")

    path = os.path.abspath(os.path.expanduser(user_path))
    if (
        user_path.endswith((os.sep, os.altsep) if os.altsep else (os.sep,))
        or os.path.isdir(path)
    ):
        path = os.path.join(path, "key.txt")
    return path


def save_key_file(path, key, overwrite=False):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    mode = "w" if overwrite else "x"
    with open(path, mode, encoding="utf-8") as key_file:
        key_file.write(key + "\n")
    print(f"Key file saved to: {path}")


def encrypt_file(source_path, random_key):
    source = os.path.abspath(source_path)
    destination = os.path.splitext(source)[0] + ".pet"
    if os.path.abspath(destination) == source:
        raise ValueError("The source file already has a .pet extension.")
    if os.path.exists(destination):
        raise FileExistsError(f"Output file already exists: {destination}")

    extension = os.path.splitext(source)[1]
    extension_bytes = extension.encode("utf-8")
    if len(extension_bytes) > 65535:
        raise ValueError("The source file extension is too long.")

    with open(source, "rb") as source_file:
        file_data = source_file.read()

    nonce = secrets.token_bytes(NONCE_LENGTH)
    payload = struct.pack(">H", len(extension_bytes)) + extension_bytes + file_data
    ciphertext = AESGCM(random_key.encode("ascii")).encrypt(
        nonce,
        payload,
        FILE_MAGIC,
    )

    with open(destination, "xb") as encrypted_file:
        encrypted_file.write(FILE_MAGIC + nonce + ciphertext)

    print(f"Encrypted file saved to: {destination}")
    print("Save this key securely. It is required to decrypt the file.")
    print("The original file was not changed.")


def decrypt_file(encrypted_path, keyinput):
    source = os.path.abspath(encrypted_path)
    if not source.lower().endswith(".pet"):
        raise ValueError("The encrypted file must have a .pet extension.")
    if len(keyinput) != KEY_LENGTH or not keyinput.isascii() or not keyinput.isalnum():
        raise ValueError("The key must be exactly 16 letters and numbers.")

    with open(source, "rb") as encrypted_file:
        encrypted_data = encrypted_file.read()

    header_length = len(FILE_MAGIC) + NONCE_LENGTH
    if (
        len(encrypted_data) < header_length + 16
        or not encrypted_data.startswith(FILE_MAGIC)
    ):
        raise ValueError("The file is not a valid PET encrypted file.")

    nonce = encrypted_data[len(FILE_MAGIC):header_length]
    try:
        payload = AESGCM(keyinput.encode("ascii")).decrypt(
            nonce,
            encrypted_data[header_length:],
            FILE_MAGIC,
        )
    except InvalidTag as error:
        raise ValueError(
            "Decryption failed: the key is incorrect or the file is damaged."
        ) from error

    if len(payload) < 2:
        raise ValueError("The encrypted file metadata is invalid.")

    extension_length = struct.unpack(">H", payload[:2])[0]
    metadata_end = 2 + extension_length
    if metadata_end > len(payload):
        raise ValueError("The encrypted file metadata is invalid.")

    try:
        extension = payload[2:metadata_end].decode("utf-8")
    except UnicodeError as error:
        raise ValueError("The stored file extension is invalid.") from error
    if (
        (extension and not extension.startswith("."))
        or os.path.basename(extension) != extension
        or "/" in extension
        or "\\" in extension
    ):
        raise ValueError("The stored file extension is invalid.")

    destination = source[:-4] + extension
    if os.path.exists(destination):
        destination = source[:-4] + ".decrypted" + extension
    with open(destination, "xb") as decrypted_file:
        decrypted_file.write(payload[metadata_end:])

    print(f"Decrypted file saved to: {destination}")
    print("Decryption Complet")


mod = input("Select a mode [e]Encrypt [d]Decryption [s]setting : ")

# File Encryption Logic
if mod == "e":
    file_path = input("Enter the path of the file to encrypt: ")
    print(f"Target File: {file_path}")
    while True:
        anser_user = input("Warning : This file will be encrypted! Do you want to continue? [Y]yes [n]no [c]change File : ")
        if anser_user == "Y":
            print("File Targeting!")
            break
        elif anser_user == "n":
            print("Encryption process aborted by user.")
            print("Exiting the program.")
            os.system("cls" if os.name == "nt" else "clear")
            exit()
        elif anser_user == "c":
            file_path = input("Enter the path of the file to encrypt: ")
            print(f"Target File: {file_path}")
        else:
            print("Invalid input. Please enter 'Y', 'n', or 'c'.")


    #last Check
    if not os.path.isfile(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        print("Exiting the program.")
        exit()
    else:
        print(f"File '{file_path}' found. Proceeding with encryption.")
        key_pathe = input("Enter the path to input the key file (e.g., /path/to/key.txt): ")
        last_check = input("Are you sure you want to encrypt this file? [Y]yes [n]no : ")
        if last_check == "Y":
            print("Starting the encryption process...")
            with open((key_pathe), "r") as key_file:
                key_contente = key_file.read().strip()
        else:
            print("Cancelled")
            exit()

    print("Encrypting the file in 5 seconds...")
    wait_time = 5
    for i in range(wait_time, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    try:
        encrypt_file(file_path, key_contente)
    except (FileExistsError, OSError, ValueError) as error:
        print(f"Encryption failed: {error}")

#Decryption Logic

elif mod == "d":
    file_path = input("Enter the path of the file to decrypt: ")
    print(f"Target File: {file_path}")
    while True:
        anser_user = input("Warning : This file will be decrypted! Do you want to continue? [Y]yes [n]no [c]change File : ")
        if anser_user == "Y":
            print("File Targeting!")
            break
        elif anser_user == "n":
            print("Decryption process aborted by user.")
            print("Exiting the program.")
            os.system("cls" if os.name == "nt" else "clear")
            exit()
        elif anser_user == "c":
            file_path = input("Enter the path of the file to decrypt: ")
            print(f"Target File: {file_path}")
        else:
            print("Invalid input. Please enter 'Y', 'n', or 'c'.")

    with open(input("Enter the path to input the key file (e.g., /path/to/key.txt): "), "r") as key_file:
        keyinput = key_file.read().strip()

    #last Check
    if not os.path.isfile(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        print("Exiting the program.")
        exit()
    else:
        print(f"File '{file_path}' found. Proceeding with decryption.")
        last_check = input("Are you sure you want to decrypt this file? [Y]yes [n]no : ")
        if last_check == "Y":
            print("Starting the decryption process...")
        else:
            print("Cancelled")
            exit()

    print("Decrypting the file in 5 seconds...")
    wait_time = 5
    for i in range(wait_time, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    try:
        decrypt_file(file_path, keyinput)
    except (FileExistsError, OSError, ValueError) as error:
        print(f"Decryption failed: {error}")

elif mod == "s":
    selectset = input("Select a setting [1]Key Settings [e]Exit and Save : ")
    if selectset == "1":
        print("Key Settings")
        print("1. Key Gen/ReGen")
        print("2. Check Keys(WIP)")
        print("e. back and Save")
        keyset = input("Select a Setting number : ")
        if keyset == "1":
           while True:
            rg = input("Do you want to generate a new key or Regenerate? [G]generate [R]regenerate [e]exit : ")
            if rg == "G":
                pathkeyy = input(
                    "Enter the key file path (include key.txt, or enter an "
                    "existing folder / folder path ending in a separator): "
                )
                try:
                    key_path = get_key_file_path(pathkeyy)
                    random_key = "".join(
                        secrets.choice(KEY_CHARACTERS) for _ in range(KEY_LENGTH)
                    )
                    save_key_file(key_path, random_key)
                except (FileExistsError, OSError, ValueError) as error:
                    print(f"Could not save the key file: {error}")

            elif rg == "R":
                pathkeyy = input("Enter the key file path to regenerate: ")
                try:
                    key_path = get_key_file_path(pathkeyy)
                    if not os.path.isfile(key_path):
                        print(f"Error: The file '{key_path}' does not exist.")
                        continue
                    random_key = "".join(
                        secrets.choice(KEY_CHARACTERS) for _ in range(KEY_LENGTH)
                    )
                    save_key_file(key_path, random_key, overwrite=True)
                except (OSError, ValueError) as error:
                    print(f"Could not regenerate the key file: {error}")
            elif rg == "e":
                break
            else:
                print("Invalid input. Please enter 'G', 'R', or 'e'.")
        if keyset == "2":
            print ("this is WIP bro sorry exit code")
            exit()
        

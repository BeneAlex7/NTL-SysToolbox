import os
import yaml
import base64
import secrets
import stat
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidKey

def secure_delete(filepath):
    """Overwrite a file with random data multiple times before deletion."""
    try:
        length = os.path.getsize(filepath)
        with open(filepath, 'r+b') as f:
            for _ in range(3):
                f.seek(0)
                f.write(os.urandom(length))
                f.flush()
                os.fsync(f.fileno())
    except OSError:
        pass  # File might not exist or be accessible, but we still try to remove

    try:
        os.remove(filepath)
    except OSError:
        pass

def get_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_disk_file(password):
    input_file = "secret.yaml"
    output_file = "secret.yaml.enc"

    if not os.path.exists(input_file):
        return f"Error: '{input_file}' not found."

    try:
        salt = os.urandom(16)
        key = get_key(password, salt)
        fernet = Fernet(key)

        with open(input_file, 'rb') as f:
            data = f.read()

        encrypted_data = fernet.encrypt(data)

        with open(output_file, 'wb') as f:
            f.write(salt + encrypted_data)
        
        secure_delete(input_file)
        return f"Success: Encrypted to '{output_file}' and deleted original."
    except Exception as e:
        return f"Encryption Error: {str(e)}"

def decrypt_disk_file(password):
    input_file = "secret.yaml.enc"
    output_file = "secret.yaml"

    if not os.path.exists(input_file):
        return f"Error: '{input_file}' not found."

    try:
        with open(input_file, 'rb') as f:
            file_data = f.read()
            
        if len(file_data) < 16:
            return "Error: File is too small or corrupted."
            
        salt = file_data[:16]
        encrypted_data = file_data[16:]

        key = get_key(password, salt)
        fernet = Fernet(key)
        
        decrypted_data = fernet.decrypt(encrypted_data)

        with open(output_file, 'wb') as f:
            f.write(decrypted_data)
        
        return f"Success: Restored '{output_file}'."
    except InvalidKey:
        return "Error: Invalid password."
    except Exception as e:
        return f"Decryption Error: {str(e)}"
        
        return f"Success: Restored '{output_file}'."
    except Exception:
        return "Error: Invalid password or corrupted file."

def load_secrets_dict(password):

    # Reads 'secret.yaml.enc' in memory
    # Raises Exception if decryption fails so main.py can retry

    input_file = "secret.yaml.enc"
    
    if not os.path.exists(input_file):
        return {}

    with open(input_file, 'rb') as f:
        file_data = f.read()
            
    if len(file_data) < 16:
        raise ValueError("File is too small or corrupted.")

    salt = file_data[:16]
    encrypted_data = file_data[16:]

    key = get_key(password, salt)
    fernet = Fernet(key)
    
    decrypted_data = fernet.decrypt(encrypted_data)
    
    return yaml.safe_load(decrypted_data) or {}
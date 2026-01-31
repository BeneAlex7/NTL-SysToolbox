import os
import yaml
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

STATIC_SALT = b'Sse5f784s8ze7fs6e8f4'

def get_key(password):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=STATIC_SALT,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_disk_file(password):
    input_file = "secret.yaml"
    output_file = "secret.yaml.enc"

    if not os.path.exists(input_file):
        return f"Error: '{input_file}' not found."

    try:
        key = get_key(password)
        fernet = Fernet(key)

        with open(input_file, 'rb') as f:
            data = f.read()

        encrypted_data = fernet.encrypt(data)

        with open(output_file, 'wb') as f:
            f.write(encrypted_data)
        
        os.remove(input_file)
        return f"Success: Encrypted to '{output_file}' and deleted original."
    except Exception as e:
        return f"Encryption Error: {str(e)}"

def decrypt_disk_file(password):
    input_file = "secret.yaml.enc"
    output_file = "secret.yaml"

    if not os.path.exists(input_file):
        return f"Error: '{input_file}' not found."

    try:
        key = get_key(password)
        fernet = Fernet(key)

        with open(input_file, 'rb') as f:
            encrypted_data = f.read()

        decrypted_data = fernet.decrypt(encrypted_data)

        with open(output_file, 'wb') as f:
            f.write(decrypted_data)
        
        return f"Success: Restored '{output_file}'."
    except Exception:
        return "Error: Invalid password or corrupted file."

def load_secrets_dict(password):

    # Reads 'secret.yaml.enc' in memory
    # Raises Exception if decryption fails so main.py can retry

    input_file = "secret.yaml.enc"
    
    if not os.path.exists(input_file):
        return {}

    key = get_key(password)
    fernet = Fernet(key)

    with open(input_file, 'rb') as f:
        encrypted_data = f.read()

    decrypted_data = fernet.decrypt(encrypted_data)
    
    return yaml.safe_load(decrypted_data) or {}
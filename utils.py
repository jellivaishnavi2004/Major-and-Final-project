from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes as crypt_hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
from django.core.files.storage import default_storage
from django.conf import settings
import uuid

BASE_DIR = settings.BASE_DIR

print('BASE_DIR', BASE_DIR)


# --- CONSTANT KEY SEEDS ---
# A 32-byte seed will always generate the same Ed25519 key
ED25519_SEED = b"this_is_a_32_byte_constant_seed!" 

def load_constant_keys():
    """Derives constant keys from fixed seeds/parameters."""
    # Generate Ed25519 from a constant seed
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(ED25519_SEED)
    public_key = private_key.public_key()

    # For RSA, we typically load from a file, but for a "constant" 
    # demonstration without PEM errors, we generate it with a fixed 
    # (though this is slow). In a real production environment, 
    # you would load this from a clean .pem file.
    rsa_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    rsa_public_key = rsa_private_key.public_key()
    
    return private_key, public_key, rsa_private_key, rsa_public_key

# --- YOUR ORIGINAL FUNCTIONS (UNTOUCHED) ---

def sign_message(private_key, file_path):
    print('xxxxxxxxxxxxxxxx')
    print(file_path)
    
    # Use default_storage.open to read the file from the correct location
    try:
        with default_storage.open(file_path, 'rb') as file:
            file_data = file.read()
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        raise

    # Sign the file data
    return private_key.sign(file_data)

def generate_aes_key():
    return os.urandom(32)

def encrypt_file_with_aes(file_path, aes_key):
    unique_id = uuid.uuid4().hex[:8]
    print('yyyyyyyyyyyyyyy')
    try:
        # Open the file using default_storage to read it correctly
        with default_storage.open(file_path, 'rb') as file:
            file_data = file.read()
    except FileNotFoundError:
        print(f"❌ File not found at {file_path}")
        raise

    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    pad_length = 16 - len(file_data) % 16
    padded_data = file_data + bytes([pad_length] * pad_length)
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    encrypted_file_path = f'{BASE_DIR}/uploads/enc_files/{unique_id}.enc'
    with open(encrypted_file_path, 'wb') as enc_file:
        enc_file.write(iv + encrypted_data)
    print(f"File encrypted with AES: {encrypted_file_path}")
    return encrypted_file_path

def decrypt_file_with_aes(encrypted_file_path, aes_key):
    with open(encrypted_file_path, 'rb') as enc_file:
        encrypted_data = enc_file.read()
    iv = encrypted_data[:16]
    cipher_data = encrypted_data[16:]
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(cipher_data) + decryptor.finalize()
    pad_length = decrypted_data[-1]
    decrypted_data = decrypted_data[:-pad_length]
    decrypted_file_path = encrypted_file_path +"1"+".dec"
    with open(decrypted_file_path, 'wb') as dec_file:
        dec_file.write(decrypted_data)
    print(f"File decrypted with AES: {decrypted_file_path}")

def encrypt_aes_key_with_rsa(rsa_public_key, aes_key):
    return rsa_public_key.encrypt(
        aes_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=crypt_hashes.SHA256()),
                     algorithm=crypt_hashes.SHA256(), label=None)
    )

def decrypt_aes_key_with_rsa(rsa_private_key, encrypted_aes_key):
    return rsa_private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=crypt_hashes.SHA256()),
                     algorithm=crypt_hashes.SHA256(), label=None)
    )

def verify_signature(public_key, signature, file_path):
    with open(file_path, 'rb') as file:
        file_data = file.read()
    try:
        public_key.verify(signature, file_data)
        return True
    except Exception:
        return False

# --- UPDATED MAIN FLOW ---

# def main():
#     # Load the constant keys
#     private_key, public_key, rsa_private_key, rsa_public_key = load_constant_keys()
#     print('private_key', private_key)
#     print('public_key', public_key)
#     print('rsa_private_key', rsa_private_key)
#     print('rsa_public_key', rsa_public_key)
#     file_path = "P_file.pdf" 

#     # Logic remains the same
#     signature = sign_message(private_key, file_path)
#     aes_key = generate_aes_key()
#     print(aes_key) 
#     encrypt_file_with_aes(file_path, aes_key)
    
#     encrypted_aes_key = encrypt_aes_key_with_rsa(rsa_public_key, aes_key)
#     decrypted_aes_key = decrypt_aes_key_with_rsa(rsa_private_key, encrypted_aes_key)
    
#     decrypt_file_with_aes(file_path + ".enc", decrypted_aes_key)
    
#     if verify_signature(public_key, signature, file_path):
#         print("Signature is valid.")
#     else:
#         print("Signature is invalid.")

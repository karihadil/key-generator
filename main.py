import secrets
import string

def generate_secret_key(length=32):
    characters = string.ascii_letters + string.digits 
    return 'sk_' + ''.join(secrets.choice(characters) for _ in range(length))

def generate_public_key(length=32):
    characters = string.ascii_letters + string.digits
    return 'pk_' + ''.join(secrets.choice(characters) for _ in range(length))

def generate_api_key(length=32):
    characters = string.ascii_letters + string.digits
    return 'api_' + ''.join(secrets.choice(characters) for _ in range(length))

secret_key = generate_secret_key()
public_key = generate_public_key()
api_key = generate_api_key()

print("Generated Secret Key (sk_):", secret_key)
print("Generated Public Key (pk_):", public_key)
print("Generated API Key (api_):", api_key)


def generate_license_key():
    characters = string.ascii_letters + string.digits
    blocks = [''.join(secrets.choice(characters) for _ in range(5)) for _ in range(5)]
    return '-'.join(blocks)
license_key = generate_license_key()
print("Generated License Key (XXXX-XXXX-XXXX):", license_key)

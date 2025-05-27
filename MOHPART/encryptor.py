import os
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
from datetime import datetime
import json

SECURE_LOG = "fichiers_securisés.json"

def derive_key(api_key: str) -> bytes:
    return hashlib.sha256(api_key.encode()).digest()

def encrypt_file(input_file: str, output_file: str, api_key: str):
    key = derive_key(api_key)
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)

    with open(input_file, 'rb') as f:
        plaintext = f.read()

    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

    with open(output_file, 'wb') as f:
        f.write(iv + ciphertext)

    print(f"\n✅ Fichier chiffré : {output_file}")

    # Enregistrer dans fichiers_securisés.json
    record = {
        "filename": output_file,
        "api_key": api_key,
        "created_at": datetime.utcnow().isoformat()
    }

    if os.path.exists(SECURE_LOG):
        with open(SECURE_LOG, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(record)

    with open(SECURE_LOG, "w") as f:
        json.dump(data, f, indent=4)

    print(f"🗃️ Enregistré dans {SECURE_LOG}")

if __name__ == "__main__":
    print("🔐 CHIFFREMENT DE FICHIER")
    input_path = input("Entrez le chemin du fichier à chiffrer : ").strip()
    api_key = input("Entrez votre clé API : ").strip()

    if not os.path.exists(input_path):
        print("❌ Le fichier spécifié n'existe pas.")
    else:
        output_path = input_path + ".enc"
        encrypt_file(input_path, output_path, api_key)
        print(f"🔒 Fichier chiffré : {output_path}")
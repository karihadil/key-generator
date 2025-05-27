import os
import hashlib
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

API_VALIDATION_URL = "http://localhost:8000/keys/validate"

def derive_key(api_key: str) -> bytes:
    return hashlib.sha256(api_key.encode()).digest()

def is_api_key_valid(api_key: str) -> bool:
    try:
        response = requests.get(f"{API_VALIDATION_URL}/{api_key}")
        if response.status_code == 200:
            return True
        else:
            print("❌ Erreur de validation : ", response.text)
            return False
    except Exception as e:
        print("❌ Connexion impossible à l'API :", e)
        return False

def decrypt_file(input_file: str, output_file: str, api_key: str):
    key = derive_key(api_key)

    with open(input_file, 'rb') as f:
        iv = f.read(16)
        ciphertext = f.read()

    cipher = AES.new(key, AES.MODE_CBC, iv)
    try:
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    except ValueError:
        print("❌ Erreur : la clé API est incorrecte ou le fichier est corrompu.")
        return

    with open(output_file, 'wb') as f:
        f.write(plaintext)

    print(f"\n✅ Fichier déchiffré : {output_file}")

if __name__ == "__main__":
    print("🔓 DÉCHIFFREMENT DE FICHIER")
    input_path = input("Entrez le chemin du fichier .enc à déchiffrer : ").strip()
    api_key = input("Entrez votre clé API : ").strip()

    if not os.path.exists(input_path):
        print("❌ Le fichier spécifié n'existe pas.")
    else:
        print("🔍 Vérification de la clé API...")
        if not is_api_key_valid(api_key):
            print("❌ Clé API invalide ou expirée. Déchiffrement annulé.")
        else:
            output_path = input_path.replace(".enc", ".dec")
            decrypt_file(input_path, output_path, api_key)
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
import json
import requests
from decryptor import decrypt_file
from encryptor import encrypt_file

app = FastAPI()

# === Configuration ===
API_VALIDATION_URL = "http://localhost:8000/keys/validate"
SECURE_LOG = "fichiers_securisés.json"
STATE_FILE = "state.json"
GRACE_PERIOD_DAYS = 7
ASSETS_TO_PROTECT = ["protected.txt"]  # Replace with real file list

# === Client States ===
FUNCTIONAL = "FUNCTIONAL"
EXPIRED_GRACE = "EXPIRED_GRACE"
ENCRYPTED_OFFLINE = "ENCRYPTED_OFFLINE"
ENCRYPTED_EXPIRED = "ENCRYPTED_EXPIRED"

# === Request Model ===
class DecryptRequest(BaseModel):
    filename: str
    api_key: str

# === Local State Functions ===
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"status": FUNCTIONAL, "last_online": datetime.utcnow().isoformat()}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def update_last_online(state):
    state["last_online"] = datetime.utcnow().isoformat()
    save_state(state)

def check_offline_duration(last_online_str):
    last_online = datetime.fromisoformat(last_online_str)
    return (datetime.utcnow() - last_online).days

# === Key Validation ===
def validate_api_key(api_key: str):
    try:
        response = requests.get(f"{API_VALIDATION_URL}/{api_key}")
        if response.status_code == 200:
            expires_at = response.json().get("expires_at")
            if expires_at:
                expires_dt = datetime.fromisoformat(expires_at)
                if datetime.utcnow() > expires_dt:
                    return False, "EXPIRED"
            return True, "VALID"
        elif response.status_code == 403:
            return False, "EXPIRED"
        return False, "INVALID"
    except Exception as e:
        print("❌ Connexion échouée :", e)
        return False, "OFFLINE"

# === Encrypt assets if needed ===
def encrypt_assets(api_key: str):
    for file in ASSETS_TO_PROTECT:
        if os.path.exists(file):
            encrypt_file(file, file + ".enc", api_key)
            os.remove(file)

# === Endpoint: Decrypt request ===
@app.post("/decrypt_file")
def decrypt_request(req: DecryptRequest):
    state = load_state()
    offline_days = check_offline_duration(state.get("last_online", datetime.utcnow().isoformat()))

    valid, status = validate_api_key(req.api_key)

    if status == "VALID":
        update_last_online(state)
        state["status"] = FUNCTIONAL
    elif status == "EXPIRED":
        if offline_days <= GRACE_PERIOD_DAYS:
            state["status"] = EXPIRED_GRACE
        else:
            state["status"] = ENCRYPTED_EXPIRED
            encrypt_assets(req.api_key)
            save_state(state)
            raise HTTPException(status_code=403, detail="⛔ License expired and grace period exceeded. Assets encrypted.")
    elif status == "OFFLINE":
        if offline_days > GRACE_PERIOD_DAYS:
            state["status"] = ENCRYPTED_OFFLINE
            encrypt_assets(req.api_key)
            save_state(state)
            raise HTTPException(status_code=403, detail="🕒 Offline too long. Assets encrypted.")
    else:
        state["status"] = ENCRYPTED_EXPIRED
        encrypt_assets(req.api_key)
        save_state(state)
        raise HTTPException(status_code=403, detail="🚫 Invalid key. Assets encrypted.")

    save_state(state)

    if not os.path.exists(req.filename):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")

    output_file = req.filename.replace(".enc", ".dec")
    decrypt_file(req.filename, output_file, req.api_key)
    return {"status": "success", "output_file": output_file}

# === Optional: Watch encrypted files and clean them if key is revoked ===
@app.get("/surveille_fichiers")
def surveiller_fichiers(background_tasks: BackgroundTasks):
    background_tasks.add_task(verifier_et_supprimer_depuis_json)
    return {"message": "Surveillance démarrée."}

def verifier_et_supprimer_depuis_json():
    if not os.path.exists(SECURE_LOG):
        print("Aucun fichier à surveiller.")
        return

    with open(SECURE_LOG, "r") as f:
        data = json.load(f)

    nouveaux = []
    for entry in data:
        filename = entry["filename"]
        api_key = entry["api_key"]

        try:
            response = requests.get(f"{API_VALIDATION_URL}/{api_key}")
            if response.status_code == 403:
                if os.path.exists(filename):
                    os.remove(filename)
                    print(f"🗑️ Supprimé : {filename}")
            else:
                nouveaux.append(entry)
        except Exception as e:
            print(f"Erreur sur {filename} : {e}")
            nouveaux.append(entry)

    with open(SECURE_LOG, "w") as f:
        json.dump(nouveaux, f, indent=4)

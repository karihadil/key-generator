import mysql.connector
import secrets
import string
from datetime import datetime

# ---------- Connect to MySQL ----------
conn = mysql.connector.connect(
    host='localhost',
    user='root',             # your MySQL username
    password='rahim2005', # your MySQL password
    database='stage'   # your MySQL database
)
cursor = conn.cursor()

# ---------- Key Generators ----------
def generate_license_key():
    characters = string.ascii_letters + string.digits + string.punctuation
    blocks = [''.join(secrets.choice(characters) for _ in range(4)) for _ in range(3)]
    return '-'.join(blocks)

def generate_public_key(length=32):
    characters = string.ascii_letters + string.digits + string.punctuation
    return 'pk_' + ''.join(secrets.choice(characters) for _ in range(length))

def generate_api_key(length=32):
    characters = string.ascii_letters + string.digits + string.punctuation
    return 'api_' + ''.join(secrets.choice(characters) for _ in range(length))

# ---------- Store Key ----------
def store_key(key_value, key_type, customer_id, status, expires_at):
    try:
        cursor.execute('''
            INSERT INTO `keys` (key_value, type, customer_id, status, expires_at)
            VALUES (%s, %s, %s, %s, %s)
        ''', (key_value, key_type, customer_id, status, expires_at))
        conn.commit()
        print(f"\n✅ Key stored successfully: {key_value}")
    except mysql.connector.Error as err:
        print(f"⚠ Error: {err}")

# ---------- Main Workflow ----------
if __name__ == "__main__":
    print("Which key do you want to generate?")
    print("1. License Key (XXXX-XXXX-XXXX)")
    print("2. Public Key (pk_...)")
    print("3. API Key (api_...)")
    choice = input("Enter 1, 2, or 3: ")

    if choice == '1':
        key = generate_license_key()
        key_type = 'license'
    elif choice == '2':
        key = generate_public_key()
        key_type = 'public'
    elif choice == '3':
        key = generate_api_key()
        key_type = 'api'
    else:
        print("❌ Invalid choice. Exiting.")
        exit()

    customer_id = input("Enter customer ID: ")
    status = input("Enter key status (e.g., active, revoked): ")

    expires_at_input = input("Enter expiration date (YYYY-MM-DD) or leave blank for no expiration: ")
    if expires_at_input.strip():
        try:
            expires_at = datetime.strptime(expires_at_input, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            print("⚠ Invalid date format. Use YYYY-MM-DD.")
            exit()
    else:
        expires_at = None

    # Store the generated key
    store_key(key, key_type, customer_id, status, expires_at)
    #///////////////////////////////////////////////////////////////////////licence
    key_to_check = input("Enter the key to check expiration: ")

try:
    query = '''
        SELECT expires_at FROM `keys` WHERE key_value = %s
    '''
    cursor.execute(query, (key_to_check,))
    result = cursor.fetchone()

    if result is None:
        print("\n❌ No such key found in the database.")
    else:
        expires_at = result[0]
        if expires_at is None:
            print("\n✅ This key has no expiration (it is valid indefinitely).")
        else:
            expires_at_dt = expires_at  # Already a datetime object from MySQL
            if expires_at_dt > datetime.now():
                print(f"\n✅ The key is NOT expired (expires on {expires_at_dt}).")
            else:
                print(f"\n❌ The key is EXPIRED (expired on {expires_at_dt}).")

except mysql.connector.Error as err:
    print(f"⚠ Database Error: {err}")
    
    cursor.close()
    conn.close()
#///////////////////////////////////////////////////////////////////api
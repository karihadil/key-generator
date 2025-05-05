import mysql.connector
import secrets
import string
from datetime import datetime

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='2004',
    database='stage'
)
cursor = conn.cursor()

def generate_license_key():
    characters = string.ascii_letters + string.digits
    blocks = [''.join(secrets.choice(characters) for _ in range(4)) for _ in range(3)]
    return '-'.join(blocks)

def generate_public_key(length=32):
    characters = string.ascii_letters + string.digits
    return 'pk_' + ''.join(secrets.choice(characters) for _ in range(length))

def generate_api_key(length=32):
    characters = string.ascii_letters + string.digits
    return 'api_' + ''.join(secrets.choice(characters) for _ in range(length))

def store_key(key_value, key_type, customer_id, status, expires_at, use_rate=0):
    try:
        current_time = datetime.now()

        # Check if expires_at is valid
        if expires_at is not None:
            expires_at_dt = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
            if expires_at_dt <= current_time:
                print("⚠ Error: Expiration date must be in the future compared to creation time.")
                return

        # Insert into database
        cursor.execute('''
            INSERT INTO `keys` (key_value, type, customer_id, status, expires_at, use_rate)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (key_value, key_type, customer_id, status, expires_at, use_rate))
        conn.commit()
        print(f"\n✅ Key stored successfully: {key_value}")

    except mysql.connector.Error as err:
        print(f"⚠ Database Error: {err}")
    except ValueError as ve:
        print(f"⚠ Date Parsing Error: {ve}")

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

    # Store the generated key with use_rate initialized to 0
    store_key(key, key_type, customer_id, status, expires_at, use_rate=0)

    cursor.close()
    conn.close()
    
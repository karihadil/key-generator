import mysql.connector
import secrets
import string
from datetime import datetime

# ---------- Connect to MySQL ----------
conn = mysql.connector.connect(
    host='localhost',
    user='root',             # your MySQL username
    password='rahim2005',    # your MySQL password
    database='stage'         # your MySQL database
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
def store_key(key_value, key_type, customer_id, status, expires_at, use_rate):
    try:
        cursor.execute('''
            INSERT INTO `keys` (key_value, type, customer_id, status, expires_at, use_rate)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (key_value, key_type, customer_id, status, expires_at, use_rate))
        conn.commit()
        print(f"\n✅ Key stored successfully: {key_value}")
    except mysql.connector.Error as err:
        print(f"⚠ Error: {err}")

# ---------- Main Workflow ----------
if __name__ == "__main__":
    print("Which key do you want to generate?")
    print("1. License Key (with expiration date)")
    print("2. Public Key (with max uses)")
    print("3. API Key (with max uses)")
    choice = input("Enter 1, 2, or 3: ")

    if choice == '1':
        key = generate_license_key()
        key_type = 'license'
        expires_at_input = input("Enter expiration date (YYYY-MM-DD): ")
        try:
            expires_at = datetime.strptime(expires_at_input, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            print("⚠ Invalid date format. Use YYYY-MM-DD.")
            exit()
        use_rate = None

    elif choice == '2' or choice == '3':
        if choice == '2':
            key = generate_public_key()
            key_type = 'public'
        else:
            key = generate_api_key()
            key_type = 'api'
        use_rate_input = input("Enter maximum allowed uses (integer): ")
        try:
            use_rate = int(use_rate_input)
            expires_at = None
        except ValueError:
            print("⚠ Invalid use rate. Must be an integer.")
            exit()
    else:
        print("❌ Invalid choice. Exiting.")
        exit()

    customer_id = input("Enter customer ID: ")
    status = input("Enter key status (e.g., active, revoked): ")

    # Store the generated key
    store_key(key, key_type, customer_id, status, expires_at, use_rate)

    # ---------- Validate Key ----------
    key_to_check = input("\nEnter a key to validate: ")

    try:
        cursor.execute('SELECT type, expires_at, use_rate FROM `keys` WHERE key_value = %s', (key_to_check,))
        result = cursor.fetchone()

        if result is None:
            print("\n❌ No such key found in the database.")
        else:
            key_type, expires_at, use_rate = result

            if key_type == 'license':
                if expires_at is None:
                    print("\n✅ License key has no expiration date (valid indefinitely).")
                else:
                    if expires_at > datetime.now():
                        print(f"\n✅ License key is NOT expired (expires on {expires_at}).")
                    else:
                        print(f"\n❌ License key is EXPIRED (expired on {expires_at}).")

            elif key_type in ['public', 'api']:
                if use_rate is None or use_rate <= 0:
                    print("\n❌ Public/API key has exhausted its allowed uses.")
                else:
                    print(f"\n✅ Public/API key is valid. Remaining uses: {use_rate}")
                    # Decrement use count
                    cursor.execute('UPDATE `keys` SET use_rate = use_rate - 1 WHERE key_value = %s', (key_to_check,))
                    conn.commit()
                    print("ℹ️  Decremented use count by 1.")

    except mysql.connector.Error as err:
        print(f"⚠ Database Error: {err}")

    finally:
        cursor.close()
        conn.close()

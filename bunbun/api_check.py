<<<<<<< HEAD:api_check.py
import mysql.connector
import secrets
import string
from datetime import datetime

=======
from datetime import datetime
import mysql.connector
import secrets
import string
>>>>>>> de685f6901121f03ffe95ae097cc62ffef0185f4:bunbun/api_check.py
def verify_api_key(input_key, customer_id):
    try:
        current_time = datetime.now()
        query = '''
            SELECT key_value, status, expires_at
            FROM `keys`
            WHERE key_value = %s AND customer_id = %s AND type = 'api'
        '''
        cursor.execute(query, (input_key, customer_id))
        result = cursor.fetchone()

        if result is None:
            print("❌ API key not found or doesn't match customer ID.")
            return False

        key_value, status, expires_at = result

        if status != 'active':
            print("❌ API key is not active.")
            return False

        if expires_at is not None:
            expires_at_dt = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
            if current_time > expires_at_dt:
                print("❌ API key has expired.")
                return False

        print("✅ API key is valid and access is granted.")
        return True

    except mysql.connector.Error as err:
        print(f"⚠ Database Error: {err}")
        return False
print("\n--- VERIFY API KEY ---")
api_key_input = input("Enter the API key to verify: ")
cust_id_input = input("Enter customer ID: ")

verify_api_key(api_key_input, cust_id_input)

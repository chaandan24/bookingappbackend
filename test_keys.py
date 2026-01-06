import requests

# ---------------------------------------------------------
# 1. PASTE YOUR KEYS HERE
# ---------------------------------------------------------
FLUTTER_PUBLIC_KEY = "key_test_us_pub_C75VMRoovrjYXtug9Renw6"  # The one inside lib/services/basis_theory_service.dart
PYTHON_SERVER_KEY  = "key_test_us_pvt_UPusvV9PGBX2VXFoegKHDJ.2189b6d4195a4ea5324eced723008158"   # The one inside your config.py

# ---------------------------------------------------------
# DIAGNOSTIC LOGIC
# ---------------------------------------------------------
def check_key(name, key):
    print(f"\n--- Checking {name} ---")
    response = requests.get("https://api.basistheory.com/applications/key", headers={"BT-API-KEY": key})
    
    if response.status_code != 200:
        print(f"❌ ERROR: Key is invalid! Status: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    data = response.json()
    print(f"✅ Key is Valid!")
    print(f"   - App Name:  {data.get('name')}")
    print(f"   - Tenant ID: {data.get('tenant_id')}  <-- CRITICAL CHECK")
    print(f"   - Type:      {data.get('type')}")
    
    # Check permissions for Server Key
    if name == "PYTHON_SERVER_KEY":
        perms = data.get('permissions', [])
        print(f"   - Permissions: {perms}")
        if 'token:read' not in perms:
            print("   ⚠️ WARNING: Missing 'token:read' permission!")
        if 'token:use' not in perms:
            print("   ⚠️ WARNING: Missing 'token:use' permission!")
            
    return data.get('tenant_id')

def test_token_creation_and_read():
    print("\n--- TEST: Can Server read what Flutter creates? ---")
    
    # 1. Create a dummy token using FLUTTER key
    payload = {
        "type": "card",
        "data": {
            "number": "4242424242424242",
            "expiration_month": "12",
            "expiration_year": "2030",
            "cvv": "123"
        }
    }
    create_resp = requests.post("https://api.basistheory.com/tokens", json=payload, headers={"BT-API-KEY": FLUTTER_PUBLIC_KEY})
    
    if create_resp.status_code != 201:
        print(f"❌ Flutter Key failed to create token: {create_resp.text}")
        return

    token_id = create_resp.json()['id']
    print(f"1. Flutter Key created token: {token_id}")

    # 2. Try to READ it using PYTHON key
    read_resp = requests.get(f"https://api.basistheory.com/tokens/{token_id}", headers={"BT-API-KEY": PYTHON_SERVER_KEY})
    
    if read_resp.status_code == 200:
        print("2. ✅ SUCCESS! Python Server Key can see the token.")
        print("   If this works here but fails in your app, the Key on PythonAnywhere is wrong/old.")
    else:
        print(f"2. ❌ FAILURE! Python Server Key CANNOT see the token.")
        print(f"   Status: {read_resp.status_code}")
        print(f"   Reason: {read_resp.text}")

# Run checks
t1 = check_key("FLUTTER_PUBLIC_KEY", FLUTTER_PUBLIC_KEY)
t2 = check_key("PYTHON_SERVER_KEY", PYTHON_SERVER_KEY)

if t1 and t2:
    if t1 == t2:
        print("\n✅ TENANT CHECK PASSED: Both keys are in the same Tenant.")
        test_token_creation_and_read()
    else:
        print("\n❌ TENANT MISMATCH DETECTED!")
        print(f"Flutter Tenant: {t1}")
        print(f"Python Tenant:  {t2}")
        print("SOLUTION: You must recreate the Python Server Key inside the Flutter Tenant.")
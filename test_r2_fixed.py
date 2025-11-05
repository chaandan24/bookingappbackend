"""
Test R2 Connection with TLS Fix
"""
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import ssl
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Your credentials
R2_ACCOUNT_ID = '3275aafe625568030be8fab8c53d7e0'
R2_ACCESS_KEY_ID = '7749c461f3731e1cdaa96e55f70eea0f'
R2_SECRET_ACCESS_KEY = 'e2c414a938a2dd8353bee3bfb5dcc649445eab44902f6c3bb721e9dbb9cbdc7d'
R2_BUCKET_NAME = 'booking-app'

print("🔍 Testing R2 Connection with SSL disabled...\n")

try:
    # Configuration to disable SSL verification
    config = Config(
        signature_version='s3v4',
        retries={'max_attempts': 3, 'mode': 'standard'}
    )
    
    # Create R2 client WITHOUT SSL verification
    r2 = boto3.client(
        's3',
        endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto',
        verify=False,  # DISABLE SSL VERIFICATION
        config=config
    )
    
    # Test 1: List buckets
    print("1️⃣ Testing authentication...")
    response = r2.list_buckets()
    print(f"   ✅ Authentication successful!")
    print(f"   Found {len(response['Buckets'])} bucket(s):")
    for bucket in response['Buckets']:
        print(f"      - {bucket['Name']}")
    
    # Test 2: Test specific bucket
    print(f"\n2️⃣ Testing bucket access...")
    try:
        response = r2.list_objects_v2(Bucket=R2_BUCKET_NAME, MaxKeys=1)
        print(f"   ✅ Bucket '{R2_BUCKET_NAME}' is accessible")
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            print(f"   ⚠️  Bucket '{R2_BUCKET_NAME}' doesn't exist")
            print(f"      Create it at: https://dash.cloudflare.com/{R2_ACCOUNT_ID}/r2/overview")
        else:
            print(f"   ❌ Error: {e.response['Error']['Code']}")
    
    # Test 3: Upload test file
    print(f"\n3️⃣ Testing upload...")
    test_key = 'test/connection-test.txt'
    r2.put_object(
        Bucket=R2_BUCKET_NAME,
        Key=test_key,
        Body=b'R2 connection test successful!',
        ContentType='text/plain'
    )
    print(f"   ✅ Upload successful: {test_key}")
    
    # Test 4: Delete test file
    print(f"\n4️⃣ Cleaning up...")
    r2.delete_object(Bucket=R2_BUCKET_NAME, Key=test_key)
    print(f"   ✅ Cleanup successful")
    
    print("\n" + "="*50)
    print("🎉 ALL TESTS PASSED!")
    print("="*50)
    print("\n⚠️  NOTE: SSL verification is disabled for testing.")
    print("   This is OK for development but needs to be fixed")
    print("   for production.\n")
    
except ClientError as e:
    print(f"\n❌ AWS Error: {e.response['Error']['Code']}")
    print(f"   Message: {e.response['Error']['Message']}")
    
    if e.response['Error']['Code'] == 'InvalidAccessKeyId':
        print("\n💡 Your Access Key ID is incorrect")
    elif e.response['Error']['Code'] == 'SignatureDoesNotMatch':
        print("\n💡 Your Secret Access Key is incorrect")
    
except Exception as e:
    print(f"\n❌ Unexpected error: {str(e)}")
    print("\n💡 Debug info:")
    print(f"   Python SSL: {ssl.OPENSSL_VERSION}")
    import sys
    print(f"   Python version: {sys.version}")
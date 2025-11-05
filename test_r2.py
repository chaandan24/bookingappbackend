"""
Test R2 Connection with Your Credentials
"""
import boto3
from botocore.exceptions import ClientError
import os

# Your credentials from screenshot
R2_ACCOUNT_ID = '3275aafe625568030be8fab8c53d7e0'
R2_ACCESS_KEY_ID = '7749c461f3731e1cdaa96e55f70eea0f'
R2_SECRET_ACCESS_KEY = 'e2c414a938a2dd8353bee3bfb5dcc649445eab44902f6c3bb721e9dbb9cbdc7d'
R2_BUCKET_NAME = 'booking-app'  # Change this to your bucket name

print("🔍 Testing R2 Connection...\n")

try:

    r2 = boto3.client(
    's3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=os.environ.get('AWS_REGION')
    # DO NOT include endpoint_url here
)
    
    # Test 1: List buckets
    print("1️⃣ Testing authentication...")
    response = r2.list_buckets()
    print(f"   ✅ Authentication successful!")
    print(f"   Found {len(response['Buckets'])} bucket(s):")
    for bucket in response['Buckets']:
        print(f"      - {bucket['Name']}")
    
    # Test 2: Test specific bucket access
    if R2_BUCKET_NAME:
        print(f"\n2️⃣ Testing bucket '{R2_BUCKET_NAME}'...")
        try:
            response = r2.list_objects_v2(Bucket=R2_BUCKET_NAME, MaxKeys=5)
            if 'Contents' in response:
                print(f"   ✅ Bucket exists with {len(response['Contents'])} object(s)")
            else:
                print(f"   ✅ Bucket exists but is empty")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                print(f"   ⚠️  Bucket '{R2_BUCKET_NAME}' doesn't exist yet")
                print(f"      Create it in the Cloudflare R2 dashboard")
            else:
                raise
    
    print("\n🎉 All tests passed! Your R2 setup is working!\n")
    
except ClientError as e:
    print(f"\n❌ Error: {e.response['Error']['Code']}")
    print(f"   Message: {e.response['Error']['Message']}\n")
except Exception as e:
    print(f"\n❌ Unexpected error: {str(e)}\n")
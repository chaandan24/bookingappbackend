"""
AWS S3 Connection Test Script
"""
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration using Environment Variables ---
AWS_REGION = os.environ.get('AWS_REGION')
S3_BUCKET_NAME = 'booking-app-chaandan' 

print(f"🔍 Testing S3 Connection to bucket '{S3_BUCKET_NAME}' in region '{AWS_REGION}'...")

try:
    # Boto3 client configuration for AWS S3
    s3_client = boto3.client(
        's3',
        # Credentials and region are read from environment variables (exported below)
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=AWS_REGION
        # Note: endpoint_url is OMITTED for official AWS S3
    )

    # Test 1: List objects in the specific bucket
    print("\n1️⃣ Testing bucket access...")
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, MaxKeys=1)
    
    if response.get('Contents'):
        print(f"   ✅ Success! Found content in bucket '{S3_BUCKET_NAME}'.")
    else:
        print(f"   ✅ Success! Bucket '{S3_BUCKET_NAME}' exists but is empty.")
    
    # Test 2: Check region consistency (optional but helpful)
    # The head_bucket operation can sometimes confirm access better than list_objects
    s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
    print("   ✅ Head Bucket request successful.")

    print("\n🎉 Connection and credentials are valid for AWS S3!")

except ClientError as e:
    error_code = e.response['Error']['Code']
    error_message = e.response['Error']['Message']

    if error_code == '403' or error_code == 'AccessDenied':
        print(f"\n❌ Error: Access Denied (Code: {error_code})")
        print("   Message: The key is likely valid, but the IAM user needs S3 access permissions.")
        print("   Action: Check your IAM User's policy for the bucket.")
    elif error_code == 'NoSuchBucket':
        print(f"\n❌ Error: No Such Bucket (Code: {error_code})")
        print("   Message: Bucket name is correct, but region might be wrong.")
        print("   Action: Double-check the region setting in your export command and the AWS console.")
    elif error_code == 'InvalidAccessKeyId':
        print(f"\n❌ Error: Invalid Access Key ID (Code: {error_code})")
        print("   Message: The key is fundamentally incorrect or deleted from AWS.")
        print("   Action: Go back to AWS IAM to create a NEW key and ensure you copy it correctly.")
    else:
        print(f"\n❌ Unexpected error: {error_code}")
        print(f"   Message: {error_message}")
    
except Exception as e:
    print(f"\n❌ General Error: {str(e)}\n")
"""
Detailed S3 Upload Test with Error Handling
"""
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import os
from dotenv import load_dotenv
from PIL import Image
import io
import traceback

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION')

print("=" * 60)
print("S3 UPLOAD DETAILED TEST")
print("=" * 60)

print(f"\n📋 Configuration:")
print(f"   Access Key: {AWS_ACCESS_KEY_ID[:10]}..." if AWS_ACCESS_KEY_ID else "   ❌ Not set")
print(f"   Bucket: {S3_BUCKET_NAME}")
print(f"   Region: {AWS_REGION}")

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME, AWS_REGION]):
    print("\n❌ Missing configuration! Check your .env file")
    exit(1)

try:
    print("\n1️⃣ Creating S3 client...")
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    print("   ✅ S3 client created")
    
    print("\n2️⃣ Testing bucket access...")
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        print(f"   ✅ Bucket '{S3_BUCKET_NAME}' is accessible")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"   ❌ Bucket '{S3_BUCKET_NAME}' does not exist")
        elif error_code == '403':
            print(f"   ❌ Access denied to bucket '{S3_BUCKET_NAME}'")
        else:
            print(f"   ❌ Error: {error_code} - {e.response['Error']['Message']}")
        print(f"\n   Full error response:\n   {e.response}")
        exit(1)
    
    print("\n3️⃣ Creating test image...")
    img = Image.new('RGB', (800, 600), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=85)
    img_bytes.seek(0)
    print("   ✅ Test image created (800x600 JPEG)")
    
    print("\n4️⃣ Uploading to S3...")
    test_key = 'test/upload-test.jpg'
    
    try:
        s3_client.upload_fileobj(
            img_bytes,
            S3_BUCKET_NAME,
            test_key,
            ExtraArgs={
                'ContentType': 'image/jpeg'
            }
        )
        print(f"   ✅ Upload successful!")
        print(f"   Key: {test_key}")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        print(f"   ❌ Upload failed!")
        print(f"   Error Code: {error_code}")
        print(f"   Error Message: {error_message}")
        print(f"\n   Full error response:")
        print(f"   {e.response}")
        print(f"\n   Possible causes:")
        
        if error_code == 'AccessDenied':
            print("   - IAM user lacks s3:PutObject permission")
            print("   - Bucket policy blocks uploads")
        elif error_code == 'InvalidAccessKeyId':
            print("   - Access key is incorrect")
        elif error_code == 'SignatureDoesNotMatch':
            print("   - Secret key is incorrect")
        elif error_code == 'NoSuchBucket':
            print("   - Bucket doesn't exist or wrong region")
        
        traceback.print_exc()
        exit(1)
    
    print("\n5️⃣ Verifying upload...")
    try:
        response = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=test_key)
        print(f"   ✅ File exists in S3")
        print(f"   Size: {response['ContentLength']} bytes")
        print(f"   Content-Type: {response['ContentType']}")
    except ClientError as e:
        print(f"   ❌ Verification failed: {e.response['Error']['Message']}")
    
    print("\n6️⃣ Generating public URL...")
    url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{test_key}"
    print(f"   📎 URL: {url}")
    print(f"\n   Open this URL in your browser to verify public access")
    
    print("\n7️⃣ Cleaning up...")
    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=test_key)
    print("   ✅ Test file deleted")
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYour S3 configuration is working correctly!")
    
except BotoCoreError as e:
    print(f"\n❌ BotoCore Error: {str(e)}")
    print(f"   This usually means a configuration or network issue")
    traceback.print_exc()
    
except Exception as e:
    print(f"\n❌ Unexpected Error: {str(e)}")
    print(f"   Error type: {type(e).__name__}")
    traceback.print_exc()
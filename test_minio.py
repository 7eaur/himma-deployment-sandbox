import os, boto3, sys
from botocore.exceptions import ClientError

s3 = boto3.client('s3',
    endpoint_url=os.environ['S3_ENDPOINT'],
    aws_access_key_id=os.environ['S3_ACCESS_KEY'],
    aws_secret_access_key=os.environ['S3_SECRET_KEY'],
    region_name='us-east-1'
)
bucket = os.environ['S3_BUCKET_NAME']

# 1. Create bucket
try:
    s3.head_bucket(Bucket=bucket)
    print(f"Bucket '{bucket}' already exists")
except ClientError:
    s3.create_bucket(Bucket=bucket)
    print(f"Bucket '{bucket}' created")

# 2. Upload real audio file
audio_path = os.path.join('apps', 'web', 'public', 'audio', 'fb-correct.mp3')
key = 'audio/test/e2e-test-upload.mp3'
with open(audio_path, 'rb') as f:
    s3.upload_fileobj(f, bucket, key, ExtraArgs={'ContentType': 'audio/mpeg'})
print(f"Uploaded: {key}")

# 3. Verify object exists
head = s3.head_object(Bucket=bucket, Key=key)
size = head['ContentLength']
print(f"Verified in MinIO: size={size} bytes, type={head['ContentType']}")

# 4. Generate presigned URL (5 min)
url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=300)
assert url.startswith(('http://', 'https://'))
print("Presigned URL generated successfully")

# 5. Save record to PostgreSQL using direct psycopg2
import psycopg2
db_url = os.environ['DATABASE_URL']
# Parse URL
from urllib.parse import urlparse
p = urlparse(db_url)
conn = psycopg2.connect(host=p.hostname, port=p.port or 5432,
    dbname=p.path.lstrip('/'), user=p.username, password=p.password)
cur = conn.cursor()
# Check table columns first
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='audio_submissions' ORDER BY ordinal_position;")
cols = [r[0] for r in cur.fetchall()]
print(f"audio_submissions columns: {cols}")
conn.close()

print("MinIO test: PASS")

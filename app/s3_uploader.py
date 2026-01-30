import boto3
import os
from dotenv import load_dotenv
load_dotenv()

S3_BUCKET = os.getenv("S3_BUCKET_NAME")

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_SERVER_PUBLIC_KEY"),
    aws_secret_access_key=os.getenv("AWS_SERVER_SECRET_KEY")
)

def upload_file(path):
    key = os.path.basename(path)
    s3.upload_file(path, S3_BUCKET, key, ExtraArgs={"ACL": "public-read"})
    return f"https://{S3_BUCKET}.s3.amazonaws.com/{key}"

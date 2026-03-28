import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import uuid


def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def generate_presigned_upload_url(file_extension: str, folder: str = "wardrobe") -> dict:
    """Generate a presigned URL for direct client-to-S3 upload."""
    s3 = get_s3_client()
    object_key = f"{folder}/{uuid.uuid4()}.{file_extension}"

    try:
        presigned_url = s3.generate_presigned_post(
            Bucket=settings.AWS_BUCKET_NAME,
            Key=object_key,
            Fields={"Content-Type": f"image/{file_extension}"},
            Conditions=[
                {"Content-Type": f"image/{file_extension}"},
                ["content-length-range", 1, 10_000_000],  # 1B – 10MB
            ],
            ExpiresIn=300,  # 5 minutes
        )
        public_url = (
            f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{object_key}"
        )
        return {"presigned_post": presigned_url, "object_key": object_key, "public_url": public_url}
    except ClientError as e:
        raise RuntimeError(f"Could not generate presigned URL: {str(e)}")


def delete_s3_object(object_key: str):
    s3 = get_s3_client()
    try:
        s3.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=object_key)
    except ClientError:
        pass  # Non-critical; log in production

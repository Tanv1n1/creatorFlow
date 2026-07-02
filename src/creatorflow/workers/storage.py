import os
import boto3
from botocore.config import Config
from creatorflow.config import settings


def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def upload_file(local_path: str, r2_key: str) -> str:
    _client().upload_file(local_path, settings.r2_bucket_name, r2_key)
    return r2_key


def download_file(r2_key: str, local_path: str) -> str:
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    _client().download_file(settings.r2_bucket_name, r2_key, local_path)
    return local_path


def delete_file(r2_key: str) -> None:
    _client().delete_object(Bucket=settings.r2_bucket_name, Key=r2_key)


def presigned_upload(r2_key: str, expires_in: int = 3600) -> str:
    return _client().generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.r2_bucket_name, "Key": r2_key},
        ExpiresIn=expires_in,
    )


def presigned_download(r2_key: str, expires_in: int = 86400) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.r2_bucket_name, "Key": r2_key},
        ExpiresIn=expires_in,
    )

"""Optional private S3 archival; local mode stores source text only in SQL."""
import os

def archive_document(org_id: str, document_id: str, title: str, body: str):
    bucket = os.getenv("DOCUMENT_BUCKET", "")
    if not bucket:
        return
    import boto3
    # IDs come from the server, never a user-supplied object path.
    boto3.client("s3").put_object(
        Bucket=bucket, Key=f"{org_id}/{document_id}.txt",
        Body=(title + "\n\n" + body).encode("utf-8"), ContentType="text/plain; charset=utf-8",
        ServerSideEncryption="AES256",
    )

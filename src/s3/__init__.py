import os
import uuid
from io import BytesIO

from aiobotocore.session import get_session

from config import S3_REGION_NAME, S3_BUCKET, AWS_SECRET_ACCESS_KEY, AWS_ACCESS_KEY_ID

session = get_session()



async def upload_image_to_s3(image: bytes) -> dict:
    image_stream = BytesIO(image)
    key = f'{uuid.uuid4()}.png'
    async with session.create_client(
        "s3",
        region_name=S3_REGION_NAME,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_access_key_id=AWS_ACCESS_KEY_ID
    ) as client:
        resp = await client.put_object(Bucket=S3_BUCKET, Key=key, Body=image_stream)
        if resp["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return {'success': True, 'key': key}
        return {'success': False, 'key': key}
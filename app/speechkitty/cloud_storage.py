import os
import traceback
import warnings
import boto3
from typing import Optional


class CloudStorage:
    region_name = "ru-central1"
    storage_endpoint = "https://storage.yandexcloud.net"
    storage_base_url = "https://storage.yandexcloud.net"

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        bucket_name: str,
        raise_exceptions: bool = False,
    ) -> None:
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.bucket_name = bucket_name
        self.raise_exceptions = raise_exceptions

    def get_client(self):
        session = boto3.session.Session(
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        return session.client(service_name="s3", endpoint_url=self.storage_endpoint)

    def upload_file(self, file_path: str, client=None) -> Optional[str]:
        file_name = os.path.basename(file_path)
        file_link = f"{self.storage_base_url}/{self.bucket_name}/{file_name}"
        if not client:
            client = self.get_client()
        try:
            client.upload_file(file_path, self.bucket_name, file_name)
        except Exception as e:
            if self.raise_exceptions:
                raise e
            else:
                warnings.warn(f"Upload error: {file_path} {traceback.format_exc()}")
                return None
        return file_link

    def delete_file(self, file_path: str, client=None) -> None:
        if not client:
            client = self.get_client()
        try:
            for_deletion = [{"Key": os.path.basename(file_path)}]
            client.delete_objects(Bucket=self.bucket_name, Delete={"Objects": for_deletion})
        except Exception as e:
            if self.raise_exceptions:
                raise e
            else:
                warnings.warn(f"Delete error: {file_path} {traceback.format_exc()}")

    async def upload_file_async(self, file_path: str, client=None) -> Optional[str]:
        # boto3 is blocking, so we run it in a separate thread
        import asyncio

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.upload_file, file_path, client)

    async def delete_file_async(self, file_path: str, client=None) -> None:
        import asyncio

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.delete_file, file_path, client)

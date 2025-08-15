import io
import asyncio
from abc import ABC, abstractmethod
from typing import Optional,Union,Dict,Type

import aioboto3
from botocore.client import Config
from botocore.exceptions import ClientError
from qcloud_cos import CosConfig,CosS3Client,CosServiceError

from app.core.config import Settings
from app.core.logger import logger

class BaseStorageService(ABC):
    """抽象存储服务基类，定义了所有存储服务必须实现的核心接口。"""

    def __init__(self,settings:Settings):
        self.settings = settings
        
    @abstractmethod
    async def generate_presigned_url_for_download(
        self, key: str, expiration: int = 3600
    ) -> Optional[str]:
        pass

    @abstractmethod
    async def generate_presigned_url_for_upload(
        self, key: str, content_type: str, expiration: int = 3600
    ) -> Optional[dict]:
        pass

    @abstractmethod
    async def download_stream(self, key: str) -> Optional[io.BytesIO]:
        pass

    @abstractmethod
    async def upload_stream(
        self, key: str, data: Union[bytes, io.BytesIO], content_type: str
    ) -> bool:
        pass

    @abstractmethod
    async def delete_file(self, key: str) -> bool:
        pass

class S3StorageService(BaseStorageService):
    """
    一个使用 aioboto3 实现的、遵循最佳实践的异步S3存储服务。
    """
    def __init__(self,settings : Settings):
        super().__init__(settings)
        self.bucket_name = settings.S3_BUCKET_NAME
        self.session = aioboto3.Session(
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION_NAME,
        )
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.s3_config = Config(s3={'addressing_style': 'virtual'})

    async def generate_presigned_url_for_download(
        self, key: str, expiration: int = 3600
    ) -> Optional[str]:
        async with self.session.client("s3", endpoint_url=self.endpoint_url,config=self.s3_config) as s3_client:
            try:
                url = await s3_client.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=expiration
                )
                return url
            except ClientError:
                logger.exception(f"Failed to generate download URL for key '{key}'")
                return None

    async def generate_presigned_url_for_upload(
        self, key: str, content_type: str, expiration: int = 3600
    ) -> Optional[dict]:
        """
        异步生成用于 PUT 上传文件的预签名URL。
        相比POST，PUT方法更简单，客户端直接向此URL发起PUT请求即可。
        """
        async with self.session.client("s3", endpoint_url=self.endpoint_url,config=self.s3_config) as s3_client:
            try:
                # 使用 generate_presigned_url 和 'put_object' 方法生成用于 PUT 上传的 URL
                url = await s3_client.generate_presigned_url(
                    ClientMethod='put_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': key,
                        'ContentType': content_type  # 在签名中指定Content-Type以增强安全性
                    },
                    ExpiresIn=expiration
                )
                return {'url': url, 'fields': {}}
            except ClientError:
                logger.exception(f"Failed to generate PUT upload URL for key '{key}'")
                return None

    async def download_stream(self, key: str) -> Optional[io.BytesIO]:
        async with self.session.client("s3", endpoint_url=self.endpoint_url, config=self.s3_config) as s3_client:
            try:
                response = await s3_client.get_object(Bucket=self.bucket_name, Key=key)
                async with response['Body'] as stream:
                    content = await stream.read()
                    logger.info(f"Successfully downloaded {len(content)} bytes from s3://{self.bucket_name}/{key}")
                    return io.BytesIO(content)
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    logger.warning(f"File not found at s3://{self.bucket_name}/{key}")
                else:
                    logger.exception(f"Failed to download file from s3://{self.bucket_name}/{key}")
                return None

    async def upload_stream(self, key: str, data: Union[bytes, io.BytesIO], content_type: str) -> bool:
        async with self.session.client("s3", endpoint_url=self.endpoint_url, config=self.s3_config) as s3_client:
            try:
                if isinstance(data, bytes):
                    file_obj = io.BytesIO(data)
                elif isinstance(data, io.BytesIO):
                    file_obj = data
                    file_obj.seek(0) # Ensure stream is at the beginning
                else:
                    raise TypeError("data must be bytes or io.BytesIO")

                await s3_client.upload_fileobj(
                    file_obj,
                    self.bucket_name,
                    key,
                    ExtraArgs={'ContentType': content_type}
                )
                logger.info(f"Successfully uploaded file to s3://{self.bucket_name}/{key}")
                return True
            except ClientError:
                logger.exception(f"Failed to upload file to s3://{self.bucket_name}/{key}")
                return False

    async def delete_file(self, key: str) -> bool:
        async with self.session.client("s3", endpoint_url=self.endpoint_url,config=self.s3_config) as s3_client:
            try:
                await s3_client.delete_object(Bucket=self.bucket_name, Key=key)
                logger.info(f"Successfully deleted s3://{self.bucket_name}/{key}")
                return True
            except ClientError:
                logger.exception(f"Failed to delete file at s3://{self.bucket_name}/{key}")
                return False

            
class COSStorageService(BaseStorageService):
    """
    使用腾讯云对象存储(COS)的服务实现。
    本实现通过 asyncio.to_thread 将同步的SDK调用转换为真正的异步非阻塞操作。
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.bucket = self.settings.TENCENT_COS_BUCKET
        try:
            config = CosConfig(
                Region=self.settings.TENCENT_COS_REGION,
                SecretId=self.settings.TENCENT_COS_SECRET_ID,
                SecretKey=self.settings.TENCENT_COS_SECRET_KEY,
            )
            self.client: CosS3Client = CosS3Client(config)
        except Exception as e:
            logger.error(f"Failed to initialize Tencent COS client: {e}")
            raise

    async def _run_in_thread(self, func, *args, **kwargs):
        """辅助函数，用于在线程池中运行阻塞函数"""
        return await asyncio.to_thread(func, *args, **kwargs)

    async def generate_presigned_url_for_download(
        self, key: str, expiration: int = 3600
    ) -> Optional[str]:
        """
        异步生成用于下载文件的预签名URL。
        """
        try:
            url = await self._run_in_thread(
                self.client.get_presigned_download_url,
                Bucket=self.bucket,
                Key=key,
                Expired=expiration
            )
            return url
        except CosServiceError as e:
            logger.error(f"Error generating download URL for {key}: {e.get_error_code()} - {e.get_error_msg()}")
            return None

    async def generate_presigned_url_for_upload(
        self, key: str, content_type: str, expiration: int = 3600
    ) -> Optional[dict]:
        """
        异步生成用于 PUT 上传文件的预签名URL。
        客户端在使用此URL进行PUT上传时，必须将请求头中的 Content-Type 设置为这里指定的 content_type。
        """
        try:
            # 将同步方法放入线程中执行，方法改为'PUT'
            url = await self._run_in_thread(
                self.client.get_presigned_url,
                Bucket=self.bucket,
                Key=key,
                Method='PUT',
                Expired=expiration
            )
            return {'url': url, 'fields': {}}
        except CosServiceError as e:
            logger.error(f"Error generating PUT upload URL for {key}: {e.get_error_code()} - {e.get_error_msg()}")
            return None

    async def download_stream(self, key: str) -> Optional[io.BytesIO]:
        """
        异步下载文件并返回一个内存中的字节流。
        """
        try:
            response = await self._run_in_thread(
                self.client.get_object,
                Bucket=self.bucket,
                Key=key
            )
            content = await self._run_in_thread(response['Body'].get_raw_stream().read)
            return io.BytesIO(content)
        except CosServiceError as e:
            if e.get_error_code() == 'NoSuchKey':
                logger.warning(f"File not found on COS: {key}")
            else:
                logger.error(f"Error downloading {key} from COS: {e.get_error_code()} - {e.get_error_msg()}")
            return None

    async def upload_stream(
        self, key: str, data: Union[bytes, io.BytesIO], content_type: str
    ) -> bool:
        """
        异步从字节流或bytes对象上传文件。
        """
        try:
            response = await self._run_in_thread(
                self.client.put_object,
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type
            )
            return 'ETag' in response
        except CosServiceError as e:
            logger.error(f"Error uploading {key} to COS: {e.get_error_code()} - {e.get_error_msg()}")
            return False

    async def delete_file(self, key: str) -> bool:
        """
        异步从COS删除指定的文件。
        """
        try:
            await self._run_in_thread(
                self.client.delete_object,
                Bucket=self.bucket,
                Key=key
            )
            return True
        except CosServiceError as e:
            logger.error(f"Error deleting {key} from COS: {e.get_error_code()} - {e.get_error_msg()}")
            return False

class StorageFactory:
    _services: Dict[str, Type[BaseStorageService]] = {
        "s3": S3StorageService,
        "cos":COSStorageService,
    }

    @staticmethod
    def get_service(provider: str, settings: Settings) -> BaseStorageService:
        service_class = StorageFactory._services.get(provider.lower())
        if not service_class:
            raise ValueError(
                f"不支持的供应商: {provider}. "
                f"可用选项: {list(StorageFactory._services.keys())}"
            )
        return service_class(settings)
# tests/services/test_storage.py
import io
import pytest
from unittest.mock import MagicMock, AsyncMock

# 模拟 botocore 的异常，因为 aioboto3 会重新抛出它们
from botocore.exceptions import ClientError

# 模拟腾讯云 SDK 的异常
from qcloud_cos.cos_exception import CosServiceError

from app.providers.storage import (
    S3StorageService,
    COSStorageService,
    StorageFactory,
)

# 从 conftest.py 导入我们的 fixture
from tests.conftest import MockSettings

# 将测试标记为 anyio，以便可以 `await`
pytestmark = pytest.mark.anyio

# ===================================================================
# S3StorageService 测试
# ===================================================================


@pytest.fixture
def mock_aioboto3_client(monkeypatch):
    """
    Mock aioboto3 的 session 和 client。
    这是测试S3服务的核心，它拦截了所有出站的网络请求。
    """
    mock_client = AsyncMock()
    # aioboto3.Session().client() 是一个异步上下文管理器
    mock_session_client = AsyncMock()
    mock_session_client.__aenter__.return_value = mock_client

    mock_session = MagicMock()
    mock_session.client.return_value = mock_session_client

    # 使用 monkeypatch 替换真实的 aioboto3.Session
    monkeypatch.setattr("aioboto3.Session", lambda **kwargs: mock_session)

    return mock_client


class TestS3StorageService:
    async def test_generate_presigned_url_for_download(
        self, mock_settings, mock_aioboto3_client
    ):
        # 准备
        service = S3StorageService(mock_settings)
        expected_url = "http://s3.presigned.url/download"
        mock_aioboto3_client.generate_presigned_url.return_value = expected_url

        # 执行
        url = await service.generate_presigned_url_for_download("test-key")

        # 断言
        assert url == expected_url
        mock_aioboto3_client.generate_presigned_url.assert_awaited_once_with(
            ClientMethod="get_object",
            Params={"Bucket": mock_settings.S3_BUCKET_NAME, "Key": "test-key"},
            ExpiresIn=3600,
        )

    async def test_generate_presigned_url_for_upload(
        self, mock_settings, mock_aioboto3_client
    ):
        # 准备
        service = S3StorageService(mock_settings)
        expected_url = "http://s3.presigned.url/upload"
        mock_aioboto3_client.generate_presigned_url.return_value = expected_url

        # 执行
        result = await service.generate_presigned_url_for_upload(
            "test-key", "image/jpeg"
        )

        # 断言
        assert result == {"url": expected_url, "fields": {}}
        mock_aioboto3_client.generate_presigned_url.assert_awaited_once_with(
            ClientMethod="put_object",
            Params={
                "Bucket": mock_settings.S3_BUCKET_NAME,
                "Key": "test-key",
                "ContentType": "image/jpeg",
            },
            ExpiresIn=3600,
        )

    async def test_download_stream_success(self, mock_settings, mock_aioboto3_client):
        # 准备
        service = S3StorageService(mock_settings)
        # 模拟 S3 返回的 Body 对象，它是一个异步流
        mock_stream = AsyncMock()
        mock_stream.read.return_value = b"file content"
        mock_body = AsyncMock()
        mock_body.__aenter__.return_value = mock_stream

        mock_aioboto3_client.get_object.return_value = {"Body": mock_body}

        # 执行
        stream = await service.download_stream("test-key")

        # 断言
        assert isinstance(stream, io.BytesIO)
        assert stream.getvalue() == b"file content"
        mock_aioboto3_client.get_object.assert_awaited_once_with(
            Bucket=mock_settings.S3_BUCKET_NAME, Key="test-key"
        )

    async def test_download_stream_not_found(self, mock_settings, mock_aioboto3_client):
        # 准备
        service = S3StorageService(mock_settings)
        error_response = {"Error": {"Code": "NoSuchKey"}}
        mock_aioboto3_client.get_object.side_effect = ClientError(
            error_response, "GetObject"
        )

        # 执行
        stream = await service.download_stream("non-existent-key")

        # 断言
        assert stream is None

    async def test_upload_stream_success(self, mock_settings, mock_aioboto3_client):
        # 准备
        service = S3StorageService(mock_settings)
        file_data = b"new file content"

        # 执行
        success = await service.upload_stream("new-key", file_data, "text/plain")

        # 断言
        assert success is True
        # upload_fileobj 接收一个类文件对象作为第一个参数
        mock_aioboto3_client.upload_fileobj.assert_awaited_once()
        # 检查调用参数
        args, kwargs = mock_aioboto3_client.upload_fileobj.call_args
        assert args[1] == mock_settings.S3_BUCKET_NAME
        assert args[2] == "new-key"
        assert kwargs["ExtraArgs"] == {"ContentType": "text/plain"}

    async def test_delete_file_failure(self, mock_settings, mock_aioboto3_client):
        # 准备
        service = S3StorageService(mock_settings)
        error_response = {"Error": {"Code": "SomeError"}}
        mock_aioboto3_client.delete_object.side_effect = ClientError(
            error_response, "DeleteObject"
        )

        # 执行
        success = await service.delete_file("key-to-delete")

        # 断言
        assert success is False
        mock_aioboto3_client.delete_object.assert_awaited_once_with(
            Bucket=mock_settings.S3_BUCKET_NAME, Key="key-to-delete"
        )


# ===================================================================
# COSStorageService 测试
# ===================================================================


@pytest.fixture
def mock_cos_client(monkeypatch):
    """Mock 腾讯云 COS S3 Client。"""
    mock_client = MagicMock()
    # 我们需要模拟 qcloud_cos.CosS3Client 这个类
    monkeypatch.setattr("app.providers.storage.CosS3Client", lambda config: mock_client)
    return mock_client


class TestCOSStorageService:
    # 注意：因为 COS SDK 是同步的，我们测试的是它被正确地 `await asyncio.to_thread` 调用
    # 所以我们 mock 的是同步方法，但测试函数本身是异步的
    async def test_generate_presigned_url_for_download(
        self, mock_settings, mock_cos_client
    ):
        # 准备
        service = COSStorageService(mock_settings)
        expected_url = "http://cos.presigned.url/download"
        mock_cos_client.get_presigned_download_url.return_value = expected_url

        # 执行
        url = await service.generate_presigned_url_for_download("test-key")

        # 断言
        assert url == expected_url
        mock_cos_client.get_presigned_download_url.assert_called_once_with(
            Bucket=mock_settings.TENCENT_COS_BUCKET, Key="test-key", Expired=3600
        )

    async def test_download_stream_failure(self, mock_settings, mock_cos_client):
        # 准备
        service = COSStorageService(mock_settings)
        # CosServiceError 需要的参数比较复杂，我们 mock 一个简单的版本
        mock_error = CosServiceError(method="", message="Error", status_code=404)
        mock_error.get_error_code = MagicMock(return_value="NoSuchKey")
        mock_cos_client.get_object.side_effect = mock_error

        # 执行
        stream = await service.download_stream("non-existent-key")

        # 断言
        assert stream is None

    async def test_upload_stream_success(self, mock_settings, mock_cos_client):
        # 准备
        service = COSStorageService(mock_settings)
        mock_cos_client.put_object.return_value = {"ETag": '"some-etag"'}

        # 执行
        success = await service.upload_stream("new-key", b"data", "text/plain")

        # 断言
        assert success is True
        mock_cos_client.put_object.assert_called_once_with(
            Bucket=mock_settings.TENCENT_COS_BUCKET,
            Key="new-key",
            Body=b"data",
            ContentType="text/plain",
        )

    async def test_delete_file_success(self, mock_settings, mock_cos_client):
        # 准备
        service = COSStorageService(mock_settings)
        # delete_object 成功时通常返回 None 或空 dict
        mock_cos_client.delete_object.return_value = {}

        # 执行
        success = await service.delete_file("key-to-delete")

        # 断言
        assert success is True
        mock_cos_client.delete_object.assert_called_once_with(
            Bucket=mock_settings.TENCENT_COS_BUCKET, Key="key-to-delete"
        )


# ===================================================================
# StorageFactory 测试
# ===================================================================


class TestStorageFactory:
    def test_get_s3_service(self, mock_settings):
        mock_settings.STORAGE_PROVIDER = "s3"
        service = StorageFactory.get_service(mock_settings)
        assert isinstance(service, S3StorageService)

    def test_get_cos_service(self, mock_settings):
        mock_settings.STORAGE_PROVIDER = "cos"
        service = StorageFactory.get_service(mock_settings)
        assert isinstance(service, COSStorageService)

    def test_get_unsupported_service(self, mock_settings):
        mock_settings.STORAGE_PROVIDER = "aliyun_oss"  # 一个不支持的 provider
        with pytest.raises(ValueError) as excinfo:
            StorageFactory.get_service(mock_settings)
        assert "不支持的供应商" in str(excinfo.value)

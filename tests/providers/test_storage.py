import io
import pytest
import aioboto3
from moto import mock_aws
from app.core.config import Settings
# 确保从正确的位置导入服务类
from app.providers.storage import S3StorageService, COSStorageService, StorageFactory

# 使用 pytest fixture 来提供可配置的 settings 对象
@pytest.fixture
def mock_settings() -> Settings:
    # 返回一个包含测试所需配置的 Settings 实例
    return Settings(
        S3_BUCKET_NAME="test-bucket",
        S3_ACCESS_KEY="testing",
        S3_SECRET_KEY="testing",
        S3_REGION_NAME="us-east-1",
        S3_ENDPOINT_URL=None, # moto 不需要真实的 endpoint
    )

@pytest.fixture
def mock_cos_settings() -> Settings:
    return Settings(
        TENCENT_COS_BUCKET="test-cos-bucket",
        TENCENT_COS_REGION="ap-guangzhou",
        TENCENT_COS_SECRET_ID="testing",
        TENCENT_COS_SECRET_KEY="testing",
    )

# --- S3Service Tests ---

@pytest.mark.asyncio
async def test_s3_upload_and_download_stream(mock_settings: Settings):
    """
    测试 S3 服务的上传和下载功能
    """
    # 修正 #1: 使用同步的 `with mock_aws()`
    with mock_aws():
        # 修正 #2: 确保所有依赖 mock 的操作都在 with 代码块内部
        
        # 1. 设置 (Setup)
        async with aioboto3.Session().client("s3", region_name=mock_settings.S3_REGION_NAME) as s3_client:
            await s3_client.create_bucket(Bucket=mock_settings.S3_BUCKET_NAME)

        service = S3StorageService(settings=mock_settings)
        test_key = "test/file.txt"
        test_content = b"Hello, S3!"
        test_stream = io.BytesIO(test_content)

        # 2. 执行 (Act)
        # 上传
        upload_success = await service.upload_stream(test_key, test_stream, "text/plain")
        
        # 下载
        downloaded_stream = await service.download_stream(test_key)

        # 3. 断言 (Assert)
        assert upload_success is True
        assert downloaded_stream is not None
        assert downloaded_stream.getvalue() == test_content

@pytest.mark.asyncio
async def test_s3_delete_file(mock_settings: Settings):
    """
    测试 S3 服务的删除功能
    """
    # 修正 #1: 使用同步的 `with mock_aws()`
    with mock_aws():
        # 修正 #2: 确保所有依赖 mock 的操作都在 with 代码块内部
        
        # 1. 设置
        bucket_name = mock_settings.S3_BUCKET_NAME
        key = "test/to_be_deleted.txt"
        async with aioboto3.Session().client("s3", region_name=mock_settings.S3_REGION_NAME) as s3_client:
            await s3_client.create_bucket(Bucket=bucket_name)
            await s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"delete me")
        
        service = S3StorageService(settings=mock_settings)

        # 2. 执行
        delete_success = await service.delete_file(key)

        # 3. 断言
        assert delete_success is True
        # 验证文件确实已被删除
        async with aioboto3.Session().client("s3", region_name=mock_settings.S3_REGION_NAME) as s3_client:
            with pytest.raises(s3_client.exceptions.NoSuchKey):
                await s3_client.get_object(Bucket=bucket_name, Key=key)

# --- COSStorageService Tests ---

@pytest.mark.asyncio
async def test_cos_upload_stream_success(mock_cos_settings: Settings, mocker):
    """
    测试 COS 服务的上传功能（成功情况）
    mocker 是 pytest-mock 提供的 fixture
    """
    # 1. 设置
    # 修正 #3: 使用正确的模块路径进行 patch
    mock_run_in_thread = mocker.patch(
        'app.providers.storage.COSStorageService._run_in_thread',
        return_value={'ETag': '"some-etag"'} # 模拟成功的返回值
    )
    
    service = COSStorageService(settings=mock_cos_settings)
    test_key = "test/file.txt"
    test_data = b"Hello, COS!"
    
    # 2. 执行
    success = await service.upload_stream(test_key, test_data, "text/plain")
    
    # 3. 断言
    assert success is True
    # 验证 mock 的方法是否被正确调用
    mock_run_in_thread.assert_called_once()
    # 可以在这里做更详细的调用参数断言
    call_args, call_kwargs = mock_run_in_thread.call_args
    assert call_kwargs['Key'] == test_key
    assert call_kwargs['Body'] == test_data

@pytest.mark.asyncio
async def test_cos_download_stream_not_found(mock_cos_settings: Settings, mocker):
    """
    测试 COS 服务的下载功能（文件不存在的情况）
    """
    # 不再需要从 qcloud_cos 导入 CosServiceError
    # from qcloud_cos.cos_exception import CosServiceError

    # 1. 设置 (Setup)
    # 创建一个模拟的异常对象 (Mock Exception)
    mock_exception = mocker.MagicMock()
    # 配置这个模拟对象的行为，使其拥有一个 get_error_code 方法
    mock_exception.get_error_code.return_value = 'NoSuchKey'

    # 模拟 _run_in_thread 方法，在被调用时抛出我们创建的模拟异常
    mocker.patch(
        'app.providers.storage.COSStorageService._run_in_thread',
        side_effect=mock_exception
    )

    service = COSStorageService(settings=mock_cos_settings)

    # 2. 执行 (Act)
    result = await service.download_stream("non_existent_key.txt")

    # 3. 断言 (Assert)
    assert result is None

# --- StorageFactory Tests ---

def test_storage_factory_get_s3_service(mock_settings: Settings):
    """测试工厂能否正确创建 S3 服务"""
    mock_settings.STORAGE_PROVIDER = "s3"
    service = StorageFactory.get_service(mock_settings)
    assert isinstance(service, S3StorageService)

def test_storage_factory_get_cos_service(mock_cos_settings: Settings):
    """测试工厂能否正确创建 COS 服务"""
    mock_cos_settings.STORAGE_PROVIDER = "cos"
    service = StorageFactory.get_service(mock_cos_settings)
    assert isinstance(service, COSStorageService)

def test_storage_factory_invalid_provider(mock_settings: Settings):
    """测试当提供商无效时工厂是否会抛出异常"""
    mock_settings.STORAGE_PROVIDER = "invalid_provider"
    with pytest.raises(ValueError, match="不支持的供应商"):
        StorageFactory.get_service(mock_settings)
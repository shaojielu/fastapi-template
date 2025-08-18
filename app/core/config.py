import os
import secrets

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    应用配置模型，使用 pydantic-settings 从环境变量和 .env 文件中加载配置。
    """
    # model_config 用于指定配置加载的行为，例如 .env 文件的路径和编码
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra='ignore')

    # --- Core Settings ---
    PROJECT_NAME: str = "Demo"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    API_V1_STR: str = "/api/v1"

    # --- Security Settings ---
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520
    JWT_ALGORITHM: str = "HS256"

    # --- CORS Settings ---
    # 配置允许访问后端的来源，为了安全，在生产环境中应指定前端域名
    # 示例: BACKEND_CORS_ORIGINS='["http://localhost:3000", "https://your-frontend.com"]'
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=["http://localhost", "http://localhost:3000", "http://127.0.0.1:3000"],
        description="List of allowed CORS origins"
    )

    # --- Database Settings ---
    # 默认使用 PostgreSQL，请在 .env 文件中覆盖此配置
    # 示例: SQLALCHEMY_DATABASE_URI=postgresql+asyncpg://user:password@host:port/db
    SQLALCHEMY_DATABASE_URI: str
    DB_ECHO: bool = False # Set to True to enable SQLAlchemy query logging (for development/debugging)

    # --- Storage Settings ---
    STORAGE_PROVIDER :str
    # S3
    S3_ACCESS_KEY: str = Field(..., description="REQUIRED: S3-compatible storage access key")
    S3_SECRET_KEY: str = Field(..., description="REQUIRED: S3-compatible storage secret key")
    S3_BUCKET_NAME: str
    S3_ENDPOINT_URL: str | None = Field(None, description="S3-compatible storage endpoint URL (e.g., for MinIO)")
    S3_REGION_NAME: str | None = Field("auto", description="S3-compatible storage region")

    # COS
    TENCENT_COS_REGION:str
    TENCENT_COS_SECRET_ID:str
    TENCENT_COS_SECRET_KEY:str
    TENCENT_COS_BUCKET :str

    # --- Logging Settings ---
    LOG_LEVEL: str = Field("INFO", description="Logging level (e.g., DEBUG, INFO, WARNING, ERROR)")
    LOG_FILE: str = Field("logs/run.log", description="Path to the log file")

# 创建一个全局可用的配置实例
settings = Settings()
if __name__ == "__main__":
    print(settings)
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    所有 Schema 的基类，自动启用 ORM 模式 (from_attributes)。
    """

    model_config = ConfigDict(from_attributes=True)

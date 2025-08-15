# FastAPI Template
一个功能齐全、可用于生产的 FastAPI 后端开发模板。

## 功能特性

- **现代 Web 框架**: 使用 [FastAPI](https://fastapi.tiangolo.com/) 构建，具备高性能和自动生成的 API 文档。
- **Python 3.12+**: 利用现代 Python 的最新特性。
- **依赖管理**: 使用 [uv](https://github.com/astral-sh/uv) 进行快速的依赖管理和虚拟环境控制。
- **数据库 ORM**: 通过 [SQLAlchemy](https://www.sqlalchemy.org/) 与数据库进行异步交互。
- **数据库迁移**: 使用 [Alembic](https://alembic.sqlalchemy.org/en/latest/) 管理数据库结构变更。
- **容器化**: 提供了 `Dockerfile`，方便使用 [Docker](https://www.docker.com/) 进行部署。
- **配置管理**: 通过 `pydantic-settings` 从环境变量 (`.env`) 中加载配置。
- **测试**: 内置了基于 [Pytest](https://docs.pytest.org/en/latest/) 的测试套件。

## 开始使用

### 环境要求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (推荐)
- [Docker](https://www.docker.com/) (可选, 用于容器化部署)

### 安装与配置

1.  **克隆代码库**
    ```bash
    git clone https://github.com/shaojielu/fastapi-template.git
    ```

2.  **创建并激活虚拟环境**
    `uv` 会自动在 `.venv` 目录中创建虚拟环境。

3.  **安装依赖**
    使用 `uv` 同步 `pyproject.toml` 中定义的依赖。
    ```bash
    uv sync
    ```

4.  **配置环境变量**
    项目启动需要一些环境变量。首先，复制一份环境文件范例：
    ```bash
    cp .env.example .env
    ```
    然后，根据你的需求修改 `.env` 文件中的配置，例如数据库连接信息、密钥等。

### 运行服务

提供了多种运行方式：

1.  **开发模式 (热重载)**
    此模式下，代码文件发生变更后服务会自动重启。
    ```bash
    uv run python -m app.api.main 
    ```
    或者
    ```bash
    uvicorn app.api.main:app --host 0.0.0.0 --port 8000 
    ```

2.  **生产模式**
    推荐使用docker方式运行

服务启动后，你可以访问以下地址：
- **API 文档 (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **备选 API 文档 (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 运行测试

执行以下命令来运行所有测试：
```bash
uv run test
```

### 数据库迁移

本项目使用 Alembic 管理数据库结构。

1.  **生成新的迁移脚本**
    当你修改了 `app/models.py` 中的 SQLAlchemy 模型后，运行此命令来自动生成迁移脚本。
    ```bash
    alembic revision --autogenerate -m "你的迁移描述"
    ```
    > 例如: `alembic revision --autogenerate -m "Add user table"`

2.  **应用迁移**
    将数据库更新到最新版本。
    ```bash
    alembic upgrade head
    ```

3.  **回滚迁移**
    回滚一个版本：
    ```bash
    alembic downgrade -1
    ```

# --- 阶段 1: 构建器 (Builder Stage) ---
# 使用一个包含完整构建工具的镜像来安装依赖
FROM python:3.13 AS builder

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# 创建一个虚拟环境
RUN python -m venv .venv

# 先只复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装依赖到虚拟环境中
# 这一步可能会需要编译器等工具，但没关系，它们不会进入最终镜像
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# --- 阶段 2: 最终镜像 (Final Stage) ---
# 使用一个极度轻量化的镜像作为最终的运行环境
FROM python:3.13-slim

WORKDIR /app

# 从构建器阶段，只复制包含所有依赖的虚拟环境
COPY --from=builder /app/.venv ./.venv

# 同样，将虚拟环境路径加入 PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

# 复制应用程序代码
# 注意：我们不再需要运行 uv sync，因为依赖已经安装好了
COPY ./app /app/app


# 暴露端口，这是一个好习惯，用于文档和自动化
EXPOSE 8000

# # 启动命令
# CMD ["fastapi", "run", "--workers", "4", "app/main.py"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

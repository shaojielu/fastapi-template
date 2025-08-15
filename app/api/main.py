from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.api.v1.api_v1 import api_router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

def custom_generate_unique_id(route: APIRoute) -> str:
    """为 OpenAPI 生成更可读的操作ID。"""
    return f"{route.tags[0]}-{route.name}"

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Default"])
async def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.main:app",reload=True,host="0.0.0.0",port=8000)

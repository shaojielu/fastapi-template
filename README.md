# FastAPI Template

A production-ready FastAPI template with user authentication, async database support, and modern Python tooling.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy 2.0+** - Async ORM with PostgreSQL support
- **JWT Authentication** - OAuth2 with Bearer tokens
- **Pydantic v2** - Data validation and settings management
- **Alembic** - Database migrations
- **Docker** - Multi-stage build for optimized images
- **Testing** - pytest with async support and coverage
- **Code Quality** - mypy, ruff for linting and formatting

## Project Structure

```
app/
├── api/                    # API layer
│   ├── deps.py            # Dependency injection
│   ├── main.py            # Router aggregation
│   └── routes/            # Endpoint implementations
├── core/                   # Core modules
│   ├── config.py          # Configuration management
│   ├── db.py              # Database setup
│   ├── exceptions.py      # Custom exceptions
│   ├── handlers.py        # Exception handlers
│   ├── logging.py         # Logging configuration
│   └── security.py        # Auth utilities
├── models/                 # SQLAlchemy models
├── schemas/                # Pydantic schemas
├── services/               # Business logic layer
└── utils/                  # Utilities
tests/                      # Test suite
scripts/                    # Development scripts
```

## Quick Start

### Prerequisites

- Python 3.13+
- PostgreSQL
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fastapi-template
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -e .
   ```

4. **Start PostgreSQL**
   ```bash
   # Using Docker Compose
   docker compose up -d postgres
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Create initial data**
   ```bash
   python app/initial_data.py
   ```

7. **Start the server**
   ```bash
   # Development
   fastapi dev app/main.py

   # Production
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

8. **Open API docs**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Or use the script
./scripts/test.sh
```

### Code Quality

```bash
# Type checking
mypy app

# Linting
ruff check app

# Formatting
ruff format app

# Or use the scripts
./scripts/lint.sh
./scripts/format.sh
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/login/access-token` | Login and get access token |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/` | List users (admin) |
| POST | `/api/v1/users/` | Create user (admin) |
| POST | `/api/v1/users/signup` | User registration |
| GET | `/api/v1/users/me` | Get current user |
| PATCH | `/api/v1/users/me` | Update current user |
| PATCH | `/api/v1/users/me/password` | Update password |
| DELETE | `/api/v1/users/me` | Delete current user |
| GET | `/api/v1/users/{id}` | Get user by ID |
| PATCH | `/api/v1/users/{id}` | Update user (admin) |
| DELETE | `/api/v1/users/{id}` | Delete user (admin) |

### Utilities

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/utils/health-check/` | Health check |
| POST | `/api/v1/utils/test-email/` | Send test email (admin) |

## Docker

### Build and Run

```bash
# Build the image
docker build -t fastapi-template .

# Run with Docker Compose
docker compose up -d

# View logs
docker compose logs -f backend
```

### Production Deployment

The Dockerfile uses a multi-stage build to create a minimal production image:

1. Builder stage: Installs dependencies with uv
2. Final stage: Copies only the virtual environment and app code

## Configuration

All configuration is done through environment variables. See `.env.example` for available options.

### Key Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | local/staging/production | local |
| `SECRET_KEY` | JWT signing key | (required) |
| `POSTGRES_*` | Database connection | (required) |
| `FIRST_SUPERUSER` | Initial admin email | (required) |
| `FIRST_SUPERUSER_PASSWORD` | Initial admin password | (required) |

## Architecture

### Layered Architecture

1. **API Layer** (`app/api/`) - HTTP handling, request/response
2. **Service Layer** (`app/services/`) - Business logic
3. **Data Layer** (`app/models/`) - Database models

### Dependency Injection

Uses FastAPI's `Depends` with `Annotated` type hints:

```python
UserServiceDep = Annotated[UserService, Depends(get_user_service)]

@router.get("/users/me")
async def get_me(user_service: UserServiceDep):
    ...
```

### Exception Handling

Custom exceptions in `app/core/exceptions.py` are automatically converted to HTTP responses by global handlers.

```python
raise NotFoundError("User not found")  # -> 404
raise AlreadyExistsError("Email taken") # -> 409
raise PermissionDeniedError("Not allowed") # -> 403
```

## License

MIT

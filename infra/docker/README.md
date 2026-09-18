# Docker Infrastructure

This directory contains Docker-related configuration files for the Jenna AI Platform.

## Services

| Service    | Image              | Port | Purpose             |
|------------|-------------------|------|---------------------|
| web        | Custom (Next.js)  | 3000 | Frontend dashboard  |
| api        | Custom (FastAPI)  | 8000 | Backend API         |
| postgres   | postgres:16-alpine| 5432 | Primary database    |
| redis      | redis:7-alpine    | 6379 | Cache & message bus |

## Usage

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Stop and remove volumes
docker compose down -v
```

## Health Checks

All services include health checks:
- **PostgreSQL**: `pg_isready`
- **Redis**: `redis-cli ping`
- **API**: HTTP GET `/api/v1/health`

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

**CRITICAL: All Python commands must be executed inside Docker containers**

- Use `docker-compose exec app <command>` for all Python operations
- Never run Python commands directly on the host system
- The application runs at port 8088 (mapped from container port 8000)
- Database runs on port 5438 (mapped from container port 5432)

### Essential Commands

```bash
# Start all services
docker-compose up -d

# Execute Python commands (always use this pattern)
docker-compose exec app python -c "from src.api.main import app; print('App loaded')"

# Run tests
docker-compose exec app pytest

# Code formatting and linting
docker-compose exec app ruff format .
docker-compose exec app ruff check .

# Check logs
docker-compose logs -f app

# Stop services
docker-compose down

# Access database shell
docker-compose exec db psql -U postgres -d bullbot_signals

# Celery monitoring
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat

```

## Architecture Overview

This is a **Clean Architecture** crypto trading signals application with strict layer separation:

### Core Layer (`src/core/`)
- **Models**: Business entities (`crypto.py`, `signals.py`)
- **Services**: Business logic (`rsi_service.py`, `rsi_calculator.py`, `signal_filter.py`)
- Contains pure business logic with no external dependencies

### Adapters Layer (`src/adapters/`)
- **External APIs**: Exchange client (`mexc_client.py`)
- Implements interfaces defined in core layer
- Handles external system integration

### API Layer (`src/api/`)
- **FastAPI application**: HTTP interface (`main.py`)
- **Routes**: Endpoint definitions (`routes/` directory)
- **Schemas**: Request/response DTOs (`schemas/` directory)

### Infrastructure
- **Database**: SQLAlchemy models and connection (`src/database/`)
- **Tasks**: Celery configuration and async tasks (`src/tasks/`)
- **Utils**: Configuration, logging, utilities (`src/utils/`)

### Key Services

1. **RSI Service** (`src/core/services/rsi_service.py`): Main business logic for RSI analysis
2. **Exchange Client**: MEXC API integration
3. **Celery Tasks**: Background processing for monitoring and data collection
4. **Trading Coins System**: Curated coin selection with automatic updates

## Exchange Integration

The system uses MEXC Exchange as the single data source:

- **MEXC**: Spot market data source (20 req/sec, no spot trading fees)

The system uses custom RSI calculation based on OHLCV data rather than direct RSI endpoints.

## Configuration

- **Environment**: All configuration via `.env` file (copy from `env.example`)
- **Settings**: Centralized in `src/utils/config.py`
- **RSI Parameters**: Configurable window sizes and thresholds
- **Exchange Selection**: Configurable default exchange per request

## Key Patterns

1. **Dependency Injection**: Services depend on interfaces, not implementations
2. **Async/Await**: All I/O operations are asynchronous
3. **Error Handling**: Exchange-specific exception classes with fallback logic
4. **Rate Limiting**: Built into exchange clients
5. **Containerization**: 100% Docker-based development and deployment

## Code Quality Standards

- **Type Hints**: Required on all functions and methods
- **Docstrings**: Portuguese documentation for all classes and methods
- **Ruff**: Code formatting (88 char line length)
- **Pytest**: Testing framework with async support
- **Logging**: Structured logging with appropriate levels (no emojis except ❌ for errors)

## Testing

- Tests located in `tests/` directory
- Use `pytest` with async support enabled
- Target >80% code coverage
- Run with: `docker-compose exec app pytest`

## Common Development Tasks

### Adding New Exchange
1. Create client in `src/adapters/`
2. Implement exchange interface
3. Add to RSI service exchange selection
4. Update configuration and documentation

### Adding New RSI Endpoint
1. Define schema in `src/api/schemas/`
2. Add route in `src/api/routes/`
3. Implement business logic in `src/core/services/`
4. Add tests for new functionality


## Resource Limits

The application is optimized for resource-constrained environments:
- App: 250MB memory limit
- Database: 128MB memory limit  
- Celery worker: 200MB memory limit
- Redis: 64MB memory limit

## Security Notes

- No sensitive data in code or logs
- Exchange API keys handled via environment variables
- All external API calls include proper error handling
- Rate limiting prevents API abuse
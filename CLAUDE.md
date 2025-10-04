# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

**CRITICAL: All Python commands must be executed inside Docker containers**

- Use `docker-compose exec celery_worker <command>` for Python operations
- Never run Python commands directly on the host system
- **No API/web server** - system runs only via Celery workers
- Database runs on port 5438 (mapped from container port 5432)

### Essential Commands

```bash
# Start all services
docker-compose up -d

# Execute Python commands (always use this pattern)
docker-compose exec celery_worker python -c "from src.tasks.celery_app import celery_app; print('Celery loaded')"

# Run tests
docker-compose exec celery_worker pytest

# Code formatting and linting
docker-compose exec celery_worker ruff format .
docker-compose exec celery_worker ruff check .

# Check worker logs
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat

# Restart workers (after code changes)
docker-compose restart celery_worker celery_beat

# Stop services
docker-compose down

# Access database shell
docker-compose exec db psql -U postgres -d bullbot_signals

```

## Architecture Overview

This is a **Celery-based** crypto trading signals application focused on background processing:

### Core Layer (`src/core/`)
- **Models**: Business entities (`crypto.py`, `signals.py`)
- **Services**: Business logic (`rsi_service.py`, calculators, filters, analyzers)
- Contains pure business logic with no external dependencies

### Services Layer (`src/services/`)
- **MEXC Client**: Exchange API integration (`mexc_client.py`)
- **MEXC Pairs Service**: Trading pairs management (`mexc_pairs_service.py`)

### Infrastructure
- **Database**: SQLAlchemy models and connection (`src/database/`)
- **Tasks**: Celery workers - ONLY entry point (`src/tasks/`)
- **Utils**: Configuration, logging, utilities (`src/utils/`)

### Key Components

1. **Celery Workers** (ONLY entry point - no API):
   - `sync_mexc_pairs`: Syncs trading pairs from MEXC every 24h
   - `monitor_rsi_signals`: Detects and saves RSI signals every 5min

2. **RSI Service** (`src/core/services/rsi_service.py`): Main business logic for RSI analysis
3. **MEXC Client** (`src/services/mexc_client.py`): MEXC API integration
4. **MEXC Pairs Service** (`src/services/mexc_pairs_service.py`): Trading pairs management
5. **Trading Coins System**: PostgreSQL-based real-time pair management

## Exchange Integration

The system uses **MEXC as the single exchange**:

- **MEXC**: Exclusive data source (20 req/sec limit, spot market)
- **Database-backed**: All trading pairs stored in PostgreSQL `trading_coins` table
- **Real-time sync**: Automatic synchronization every 5 minutes via Celery
- **Smart validation**: Symbols validated against `base_asset/USDT` pairs with `is_spot_trading_allowed=true`

All analysis uses custom RSI calculation based on OHLCV data from MEXC API.

## Configuration

- **Environment**: All configuration via `.env` file (copy from `env.example`)
- **Settings**: Centralized in `src/utils/config.py`
- **RSI Parameters**: Configurable window sizes and thresholds
- **Exchange Selection**: Configurable default exchange per request

## Key Patterns

1. **Dependency Injection**: Services depend on interfaces, not implementations
2. **Async/Await**: All I/O operations are asynchronous
3. **Error Handling**: MEXC-specific exception classes with proper logging
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

### Adding New Indicator/Signal
1. Create calculator in `src/core/services/`
2. Update RSI service to include new indicator
3. Add to confluence analyzer if needed
4. Update signal data builder
5. Add tests for new functionality

### Modifying Worker Behavior
1. Edit tasks in `src/tasks/monitor_tasks.py`
2. Update Celery beat schedule in `src/tasks/celery_app.py`
3. Test with: `docker-compose restart celery_worker celery_beat`


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
"""API-specific dependencies for FastAPI routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.database.connection import get_db

# Database dependencies
DatabaseDep = Annotated[Session, Depends(get_db)]

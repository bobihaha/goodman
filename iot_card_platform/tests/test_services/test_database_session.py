from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db import database
from app.utils.exceptions import AuthException


class _SessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, traceback):
        return False


@pytest.fixture
def session(monkeypatch):
    value = MagicMock()
    value.commit = AsyncMock()
    value.rollback = AsyncMock()
    monkeypatch.setattr(database, "AsyncSessionLocal", lambda: _SessionContext(value))
    return value


@pytest.mark.asyncio
async def test_business_exception_rolls_back_without_database_error_log(session, monkeypatch):
    log_exception = MagicMock()
    monkeypatch.setattr(database.logger, "exception", log_exception)
    dependency = database.get_db()

    assert await dependency.__anext__() is session
    with pytest.raises(AuthException):
        await dependency.athrow(AuthException())

    session.rollback.assert_awaited_once_with()
    session.commit.assert_not_awaited()
    log_exception.assert_not_called()


@pytest.mark.asyncio
async def test_unexpected_exception_rolls_back_and_logs_database_error(session, monkeypatch):
    log_exception = MagicMock()
    monkeypatch.setattr(database.logger, "exception", log_exception)
    dependency = database.get_db()

    assert await dependency.__anext__() is session
    error = RuntimeError("connection lost")
    with pytest.raises(RuntimeError, match="connection lost"):
        await dependency.athrow(error)

    session.rollback.assert_awaited_once_with()
    session.commit.assert_not_awaited()
    log_exception.assert_called_once_with("Database transaction failed: %s", error)

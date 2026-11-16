from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import text

from core.database import engine
from core.storage import get_storage

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION") != "1",
        reason="Set RUN_INTEGRATION=1 and fill server/.env to run integration tests.",
    ),
]


def test_database_connection():
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1


def test_r2_round_trip():
    storage = get_storage()
    key = f"conversions/_smoke/{uuid.uuid4()}/probe.txt"
    data = b"graphia storage probe"
    storage.put_bytes(key, data, "text/plain")
    try:
        info = storage.head(key)
        assert info is not None
        assert info.size == len(data)
        assert storage.read_range(key, 0, len(data) - 1) == data
        assert storage.presign_get(key, "probe.txt", 60).startswith("http")
    finally:
        storage.delete(key)

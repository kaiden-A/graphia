"""Shared infrastructure used by Service A and Service B."""

import os

# Windows Application Control can block SQLAlchemy's optional C extensions.
# The pure-Python fallback is fast enough for this app's small workload.
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")

import os
import sys
from pathlib import Path

from app import config

# shortcut: the pure-Python psycopg driver loads libpq.dll from the local PostgreSQL install,
# because Windows Application Control blocks the psycopg-binary DLL on the team's machines.
# This runs before any module imports psycopg. Switch the dependency to psycopg[binary] on
# machines without that policy.
if sys.platform == "win32" and Path(config.PG_BIN).is_dir():
    os.environ["PATH"] = config.PG_BIN + os.pathsep + os.environ.get("PATH", "")

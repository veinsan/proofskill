import os
import sys
from pathlib import Path

from app import config

# The pure-Python psycopg driver loads libpq.dll from the local PostgreSQL install on Windows,
# because Windows Application Control blocks the psycopg-binary DLL on the team's machines.
# This runs before any module imports psycopg. Elsewhere (Render, B-05) pyproject.toml installs
# psycopg[binary], which bundles libpq.
if sys.platform == "win32" and Path(config.PG_BIN).is_dir():
    os.environ["PATH"] = config.PG_BIN + os.pathsep + os.environ.get("PATH", "")

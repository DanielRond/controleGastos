"""API HTTP (FastAPI): specs/api. Exige o extra `web`."""

from .app import criar_app
from .config import Configuracao

__all__ = ["Configuracao", "criar_app"]

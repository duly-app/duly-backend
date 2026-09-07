from .auth import create_auth_bp
from .index import bp as main_bp

__all__ = [
    "create_auth_bp",
    "main_bp",
]

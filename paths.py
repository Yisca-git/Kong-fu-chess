"""Single source of truth for the project root and top-level asset paths."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_ROOT  = PROJECT_ROOT / "assets2"

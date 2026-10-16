from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = PROJECT_ROOT / "data"
DEFAULT_DATA_DIR = DATA_ROOT / "full"
DEFAULT_DATABASE_PATH = DATA_ROOT / "generated" / "fairtoy.sqlite3"


@dataclass(frozen=True)
class ImportSettings:
    """Filesystem locations used by the local setup command."""

    data_dir: Path = DEFAULT_DATA_DIR
    database_path: Path = DEFAULT_DATABASE_PATH

    @classmethod
    def from_values(
        cls,
        *,
        data_dir: str | Path | None = None,
        database_path: str | Path | None = None,
    ) -> "ImportSettings":
        return cls(
            data_dir=Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR,
            database_path=(
                Path(database_path)
                if database_path is not None
                else DEFAULT_DATABASE_PATH
            ),
        )

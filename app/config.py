from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = APP_DIR / "config.ini"
EXAMPLE_CONFIG_PATH = APP_DIR / "config.example.ini"
LOG_DIR = APP_DIR / "logs"


@dataclass(frozen=True)
class AppConfig:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    retailer_id: int
    store_name: str
    poll_seconds: int
    config_path: Path = CONFIG_PATH

    @property
    def is_ready(self) -> bool:
        return (
            bool(self.db_host)
            and bool(self.db_name)
            and bool(self.db_user)
            and self.retailer_id > 0
        )


def _get(parser: configparser.ConfigParser, section: str, key: str, default: str = "") -> str:
    env_key = f"{section}_{key}".upper()
    return os.getenv(env_key) or os.getenv(key.upper()) or parser.get(section, key, fallback=default)


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    parser = configparser.ConfigParser()
    if path.exists():
        parser.read(path)

    db_port = int(_get(parser, "database", "port", "3306") or "3306")
    retailer_id = int(_get(parser, "retailer", "retailer_id", "0") or "0")
    poll_seconds = int(_get(parser, "sync", "poll_seconds", "10") or "10")

    return AppConfig(
        db_host=_get(parser, "database", "host"),
        db_port=db_port,
        db_name=_get(parser, "database", "name"),
        db_user=_get(parser, "database", "user"),
        db_password=_get(parser, "database", "password"),
        retailer_id=retailer_id,
        store_name=_get(parser, "retailer", "store_name", f"Retailer {retailer_id or ''}").strip(),
        poll_seconds=max(5, poll_seconds),
        config_path=path,
    )

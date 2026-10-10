import os
from dataclasses import dataclass

CODE_ALPHABET = "23456789abcdefghjkmnpqrstuvwxyz"


@dataclass(frozen=True)
class Settings:
    db_path: str = "shortlink.db"
    base_url: str = "http://localhost:8000"
    # Short codes: 6 characters from an alphabet without 0/o, 1/l/i.
    code_length: int = 6
    code_alphabet: str = CODE_ALPHABET
    # The team's timezone. Analytics days and dashboard periods use it.
    timezone: str = "America/New_York"
    redirect_cache_size: int = 10_000
    trust_proxy_headers: bool = False
    seed_demo_data: bool = True
    log_level: str = "INFO"


def load_settings() -> Settings:
    return Settings(
        db_path=os.environ.get("SHORTLINK_DB", "shortlink.db"),
        base_url=os.environ.get("SHORTLINK_BASE_URL", "http://localhost:8000"),
        timezone=os.environ.get("SHORTLINK_TZ", "America/New_York"),
        trust_proxy_headers=os.environ.get("SHORTLINK_TRUST_PROXY", "0") == "1",
        seed_demo_data=os.environ.get("SHORTLINK_SEED", "1") != "0",
        log_level=os.environ.get("SHORTLINK_LOG_LEVEL", "INFO"),
    )

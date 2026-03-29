from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str
    database_name: str
    frontend_origin: str
    supabase_url: str
    supabase_service_key: str
    supabase_bucket: str
    use_memory_db: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    mongodb_uri = os.getenv("MONGODB_URI", "").strip()
    return Settings(
        mongodb_uri=mongodb_uri,
        database_name=os.getenv("MONGODB_DB_NAME", "bee2gether"),
        frontend_origin=os.getenv("FRONTEND_ORIGIN", "*"),
        supabase_url=os.getenv("SUPABASE_URL", "").strip(),
        supabase_service_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
        supabase_bucket=os.getenv("SUPABASE_BUCKET", "event-images").strip() or "event-images",
        use_memory_db=os.getenv("USE_MEMORY_DB", "").lower() == "true" or not mongodb_uri,
    )

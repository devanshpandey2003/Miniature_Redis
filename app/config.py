"""
Central configuration. Reads from environment variables (and a local .env
file, if present), so you never hardcode paths/ports/secrets in your code.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    host: str = "127.0.0.1"
    port: int = 8000

    aof_path: str = "data/appendonly.aof"      # where the append-only log lives
    expiry_sweep_interval: float = 1.0          # seconds between expired-key sweeps

    api_key: str = "dev-secret-key"             # change this in production!


# A single shared instance — import `settings` anywhere you need config.
settings = Settings()

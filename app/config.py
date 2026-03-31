from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    api_key: str = "change-me-in-production"
    public_base_url: str = "http://127.0.0.1:8000"
    output_dir: str = "storage/outputs"
    cors_allow_origins: str = "*"
    max_preview_rows: int = 25
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_allow_origins.strip() == "*":
            return ["*"]
        return [v.strip() for v in self.cors_allow_origins.split(",") if v.strip()]

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir)

settings = Settings()

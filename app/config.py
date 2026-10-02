from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    admin_ids: str = ""
    database_path: str = "./data/stol_ai.sqlite3"
    public_webapp_url: str = ""
    generation_provider: str = "mock"
    openai_api_key: str = ""
    openai_image_model: str = "gpt-image-1"
    free_generations: int = 1

    @property
    def admins(self) -> set[int]:
        return {int(x.strip()) for x in self.admin_ids.split(",") if x.strip().isdigit()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


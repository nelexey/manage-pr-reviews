from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_host: str = "0.0.0.0"
    app_port: int = 8080

    db_user: str = "postgres"
    db_pass: str = "1234"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "pr_db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def api_url(self) -> str:
        return f"http://{self.app_host}:{self.app_port}"


settings = Settings()

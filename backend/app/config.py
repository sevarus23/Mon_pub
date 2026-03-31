from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "iu_parsers"
    ENVIRONMENT: str = "LOCAL"

    POSTGRES_USER: str = "iu_parsers"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_HOST: str = "app_db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "iu_parsers"

    CROSSREF_EMAIL: str = "t.bektleuov@innopolis.university"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

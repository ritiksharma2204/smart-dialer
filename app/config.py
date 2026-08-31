from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://dialer:dialer@localhost:5432/smart_dialer"
    )


settings = Settings()
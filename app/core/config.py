from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:password@localhost:5432/learning_app"
    jwt_secret: str = "development-only-change-me"
    cookie_secure: bool = False
    frontend_origins: str = "http://127.0.0.1:8000,http://localhost:8000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

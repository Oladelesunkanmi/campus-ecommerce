from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://campus:campus@db:5432/cart_db"
    BCRYPT_ROUNDS: int = 10
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_TIMEOUT: int = 30
    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRY_MINUTES: int = 60
    PAYMENT_DELAY_MS: int = 50
    WORKERS: int = 1
    LOG_LEVEL: str = "warning"


settings = Settings()

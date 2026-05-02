from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "thrift_central"

    # Instagram / Meta App
    INSTAGRAM_APP_ID: str
    INSTAGRAM_APP_SECRET: str
    INSTAGRAM_REDIRECT_URI: str
    INSTAGRAM_WEBHOOK_VERIFY_TOKEN: str

    # App
    APP_ENV: str = "development"


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 資料庫：初期 sqlite，部署換 Neon PostgreSQL 只改這行（見 reference/backend/database.md）
    database_url: str = "sqlite:///./data/app.db"

    # 認證（JWT）
    jwt_secret: str = "dev-secret-change-me"
    jwt_expire_minutes: int = 60 * 24 * 30  # 30 天，手機免常重登

    app_env: str = "dev"  # dev / prod


settings = Settings()

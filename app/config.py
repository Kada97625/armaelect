from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "ARMAELECT"
    app_version: str = "2.0.0"
    app_description: str = "Plateforme de Génération Automatique de Devis et Mémoires Techniques"

    jwt_secret: str = "changez-moi-en-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    admin_password_hash: str = "$2b$12$VEx9g6uZkZf6Xz6hK3yY.eu/05OhM/6XqDFX1YhbAt3T5VDvNz6Xe"

    database_url: str = "sqlite:///./app.db"

    openai_api_key: str = ""
    default_llm_model: str = "gpt-4o"

    default_monthly_quota: int = 100

    reseller_brand_name: str = "ARMAELECT"
    reseller_contact_email: str = "contact@armaelect.app"

    cloud_sql_connection_name: str = ""
    db_user: str = "armaelect"
    db_password: str = ""
    db_name: str = "armaelect"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
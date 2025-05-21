from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    DATABASE_PUBLIC_URL: str

    # Auth
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    # Stripe
    stripe_secret_key: str
    stripe_public_key: str
    domain: str

    class Config:
        env_file = ".env"

settings = Settings()

from dotenv import load_dotenv
load_dotenv()

import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 10080))
    ENV: str = os.getenv("ENV", "development")
    DRIVER:str =os.getenv("DRIVERF")
    DB_HOST:int =os.getenv("DB_FHOST")
    DB_USER:str =os.getenv("DB_FUSERNAME")
    DB_PORT:str = os.getenv("DB_FPORT")
    DB_PASSWORD:str=os.getenv("DB_FPASSWORD")
    DB_NAME:str=os.getenv("DB_FNAME")
    CORS_ALLOWED_ORIGINS:list=os.getenv("CORS_ALLOWED_ORIGINS")
    CORS_ALLOWED_HEADERS:list=os.getenv("CORS_ALLOWED_HEADERS")
    CORS_ALLOW_CREDENTIALS:bool=os.getenv("CORS_ALLOW_CREDENTIALS")
    CORS_ALLOWED_METHODS:list=os.getenv("CORS_ALLOWED_METHODS")

settings = Settings()
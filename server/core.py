# backend/app/core.py
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

# Lấy MONGODB_URL từ biến môi trường
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# Kiểm tra xem MONGODB_URL có tồn tại không
if not MONGODB_URL:
    raise ValueError("MONGODB_URL environment variable not set.")

class Settings(BaseSettings):
    # MONGODB_URL sẽ sử dụng username/password bạn đã đặt
    MONGODB_URL: str = MONGODB_URL # Thêm dấu / ở cuối nếu cần
    DATABASE_NAME: str = DATABASE_NAME 

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8' # Thêm dòng này nếu .env có ký tự đặc biệt

settings = Settings()
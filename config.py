"""
IEMS Configuration

This file contains configuration settings for the application.
"""

import os
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Base directory of the project

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY","development-secret-key",)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app","static", "uploads") # Directory to store uploaded files
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif","webp"} # Image file extensions allowed
    # -----------------------------------------------------
    # CACHE (Redis / Upstash)
    # -----------------------------------------------------
    #
    # CACHE_ENABLED must be true for any caching to
    # happen. When false, cache_* functions are no-ops
    # and the app falls through to the database.

    REDIS_URL = os.getenv("REDIS_URL")
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "false").lower() == "true"
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "60"))

"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://localhost/domain_config'
    )
    
    # Redis (optional)
    REDIS_URL = os.environ.get('REDIS_URL', None)
    REDIS_TTL = int(os.environ.get('REDIS_TTL', 3600))
    
    # Default language
    DEFAULT_LANGUAGE = 'zh-CN'
    SUPPORTED_LANGUAGES = ['zh-CN', 'en-US', 'ja-JP', 'zh-TW', 'th-TH']
    
    # Admin password (None = no auth required)
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///dev.db'
    )


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

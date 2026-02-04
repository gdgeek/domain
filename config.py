"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


def get_database_url():
    """构建数据库连接 URL"""
    # 优先使用 DATABASE_URL
    if os.environ.get('DATABASE_URL'):
        return os.environ.get('DATABASE_URL')
    
    # 使用分开的配置构建 MySQL URL
    db_host = os.environ.get('DB_HOST')
    if db_host:
        db_user = os.environ.get('DB_USER', 'root')
        db_password = os.environ.get('DB_PASSWORD', '')
        db_port = os.environ.get('DB_PORT', '3306')
        db_name = os.environ.get('DB_NAME', 'domain_config')
        return f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4'
    
    # 默认 SQLite
    return 'sqlite:///data/app.db'


def get_redis_url():
    """构建 Redis 连接 URL"""
    # 优先使用 REDIS_URL
    if os.environ.get('REDIS_URL'):
        return os.environ.get('REDIS_URL')
    
    # 检查是否启用 Redis
    redis_enabled = os.environ.get('REDIS_ENABLED', '').lower() in ('true', '1', 'yes')
    if not redis_enabled:
        return None
    
    # 使用分开的配置构建 Redis URL
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = os.environ.get('REDIS_PORT', '6379')
    redis_password = os.environ.get('REDIS_PASSWORD', '')
    
    if redis_password:
        return f'redis://:{redis_password}@{redis_host}:{redis_port}/0'
    return f'redis://{redis_host}:{redis_port}/0'


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = get_database_url()
    
    # Redis (optional)
    REDIS_URL = get_redis_url()
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
    ADMIN_PASSWORD = None  # 测试环境禁用认证


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

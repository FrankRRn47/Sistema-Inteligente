import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://username:password@127.0.0.1:3306/databaseia",
    )
    SQLALCHEMY_FALLBACK_URI = os.getenv(
        "FALLBACK_DATABASE_URL",
        f"sqlite:///{(BASE_DIR.parent / 'instance' / 'databaseia_dev.db').resolve()}",
    )
    ALLOW_DB_FALLBACK = os.getenv("ALLOW_DB_FALLBACK", "true").lower() in {"1", "true", "yes"}
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PROPAGATE_EXCEPTIONS = True
    JSON_SORT_KEYS = False
    ANALYTICS_LIMIT = int(os.getenv("ANALYTICS_LIMIT", "10"))
    MEDIA_STORAGE_ROOT = str(
        Path(os.getenv("MEDIA_STORAGE_ROOT", BASE_DIR.parent / "tracked" / "session_media")).resolve()
    )
    MEDIA_RAW_SUBDIR = os.getenv("MEDIA_RAW_SUBDIR", "raw")
    MEDIA_SNAPSHOT_SUBDIR = os.getenv("MEDIA_SNAPSHOT_SUBDIR", "snapshots")
    TRACKED_ROOT = str(Path(os.getenv("TRACKED_ROOT", BASE_DIR.parent / "tracked")).resolve())
    SESSION_STREAM_SUBDIR = os.getenv("SESSION_STREAM_SUBDIR", "session_stream")
    SESSION_EMOTION_SUBDIR = os.getenv("SESSION_EMOTION_SUBDIR", "emotion_class")
    SESSION_SNAPSHOT_INTERVAL = int(os.getenv("SESSION_SNAPSHOT_INTERVAL", "5"))
    SESSION_VIDEO_FPS = int(os.getenv("SESSION_VIDEO_FPS", "12"))


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config(env_name: str | None = None):
    env = env_name or os.getenv("FLASK_ENV", "development").lower()
    return config_by_name.get(env, DevelopmentConfig)

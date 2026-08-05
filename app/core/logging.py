import logging
import sys
from app.config.settings import settings

def setup_logging():
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Mute noisy third-party debug loggers (aiosqlite, sqlalchemy, etc.)
    noisy_loggers = [
        "aiosqlite",
        "sqlalchemy",
        "sqlalchemy.engine",
        "sqlalchemy.engine.Engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
        "asyncpg",
        "watchfiles",
        "httpx"
    ]
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

logger = logging.getLogger("ofc_hr")

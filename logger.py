import logging
import sys

def setup_logger(name: str = "WeatherProducer", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level.upper())

    if logger.handlers.clear()  # Prevent duplicates

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s %(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def log_success(logger: logging.Logger, message: str, **kwargs):
    extra = " | ".join(f"{k}: {v}" for k, v in kwargs.items())
    logger.info(f"✅ {message} | {extra}" if kwargs else f"✅ {message}")

def log_error(logger: logging.Logger, exc: Exception, message: str = ""):
    logger.error(f"❌ {message}: {exc}" if message else f"❌ {exc}")

def log_warning(logger: logging.Logger, message: str):
    logger.warning(f"⚠️ {message}")

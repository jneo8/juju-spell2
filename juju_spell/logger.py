import logging

from loguru import logger



__all__ = ["get_logger"]


def get_logger() -> logging.Logger:
    return logger

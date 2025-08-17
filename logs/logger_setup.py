import logging
import os
from datetime import datetime


def get_logger(name: str, level=logging.INFO, logs_dir=None):
    """Return a logger that writes daily log files into logs_dir (default: ./logs).

    Log file name format: <name>_YYYY_MM_DD.log
    Multiple handlers are protected against double-adding.
    """
    if logs_dir is None:
        # logs directory is sibling of repo root logs folder
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = base_dir

    os.makedirs(logs_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    date_str = datetime.now().strftime('%Y_%m_%d')
    log_filename = f"{name}_{date_str}.log"
    log_path = os.path.join(logs_dir, log_filename)

    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

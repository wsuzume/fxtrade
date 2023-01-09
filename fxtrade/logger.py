import logging

from datetime import datetime
from pytz import timezone

def custom_time(*args):
    return datetime.now(timezone('Asia/Tokyo')).timetuple()

def getLogger(name,
        filename,
        console_level=logging.DEBUG,
        file_level=logging.DEBUG):
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger
    
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %z')
    console_formatter.converter = custom_time
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(console_handler)

    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %z')
    file_formatter.converter = custom_time
    file_handler = logging.handlers.TimedRotatingFileHandler(filename=filename, when='D', interval=1)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(file_handler)
    
    return logger
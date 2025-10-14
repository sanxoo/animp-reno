import tomllib
import logging, logging.handlers
import pathlib

from common import cipher

with open("settings.toml", "rb") as toml:
    settings = tomllib.load(toml)

_kws = ["password"]

def decrypt(d):
    for k, v in d.items():
        if isinstance(v, dict): d[k] = decrypt(v)
        else: d[k] = cipher.decrypt(v) if k in _kws else v
    return d

settings = decrypt(settings)

def add_logger(name, filename):
    handler = logging.handlers.RotatingFileHandler(
        filename=pathlib.Path(settings["ace"]["log"]) / filename,
        mode="a",
        maxBytes=10_000_000,
        backupCount=9
    )
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(filename)s:%(lineno)03d - %(message)s"
        )
    )
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

def set_logger(filename):
    add_logger(None, filename)


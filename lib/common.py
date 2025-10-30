import tomllib
import logging, logging.handlers
import pathlib
import signal

from lib import cipher

def decrypt(d, kws):
    for k, v in d.items():
        if isinstance(v, dict): d[k] = decrypt(v, kws)
        else: d[k] = cipher.decrypt(v) if k in kws else v
    return d

def get_config(path, kws):
    with open(path, "rb") as toml:
        config = tomllib.load(toml)
    return decrypt(config, kws)

config = get_config("CONF/animp.toml", ["password"])

def add_logger(name, filename):
    handler = logging.handlers.RotatingFileHandler(
        filename=pathlib.Path(config["log"]) / filename,
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

def set_signal_stop(func):
    def stop(signum, frame):
        logging.info(f"signal {signum}, stop")
        func()
    signal.signal(signal.SIGTERM, stop)


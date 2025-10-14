import logging
import time
import threading
import datetime

from common.config import settings, set_logger
from daycheck import db

def get_week_of_month(now):
    weekday_of_first_day = now.replace(day=1).weekday()
    if weekday_of_first_day < 4:
        return (now.day + weekday_of_first_day - 1) // 7 + 1
    if 7 - weekday_of_first_day < now.day:
        return (now.day + weekday_of_first_day - 1) // 7
    last_day_of_last_month = now - datetime.timedelta(days=now.day)
    return get_week_of_month(last_day_of_last_month)

def produce():
    now = datetime.datetime.now()
    params = {
        "date": now.strftime("%Y%m%d"),
        "time": now.strftime("%H%M"),
        "isoweekday": now.isoweekday(),
        "day_of_month": now.day,
        "week_of_month": get_week_of_month(now),
        "team_id": settings["team_id"],
    }
    times = {
        "min": now.strftime("%Y-%m-%d %H:%M"),
        "evt": now.strftime("%Y%m%d%H%M%S"),
    }
    try:
        logging.info(f"produce {times['evt']} {params}")
        reserved_list = db.get_reserved_list(params)
        logging.info(f"produce {len(reserved_info)} reserved items")
        db.insert_check_list(reserved_list, times)
        logging.info(f"produce {times['evt']} done")
    except:
        logging.exception("")

def run():
    intv = 60
    tick = time.time() // intv * intv + intv
    while 1:
        if tick < time.time():
            threading.Thread(target=produce).start()
            tick += intv
        time.sleep(1)


if __name__ == "__main__":
    set_logger("daycheck_producer.log")
    try:
        run()
    except:
        logging.exception("")


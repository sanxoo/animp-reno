import logging
import time
import datetime
import threading

from lib.common import config, set_logger, set_signal_stop
from bin.daily_check import db

def get_week_of_month(now):
    weekday_of_first_day = now.replace(day=1).weekday()
    if weekday_of_first_day < 4:
        return (now.day + weekday_of_first_day - 1) // 7 + 1
    if 7 - weekday_of_first_day < now.day:
        return (now.day + weekday_of_first_day - 1) // 7
    last_day_of_last_month = now - datetime.timedelta(days=now.day)
    return get_week_of_month(last_day_of_last_month)

def produce():
    try:
        now = datetime.datetime.now()
        params = {
            "date": now.strftime("%Y%m%d"),
            "time": now.strftime("%H%M"),
            "isoweekday": now.isoweekday(),
            "day_of_month": now.day,
            "week_of_month": get_week_of_month(now),
            "team_id": config["team_id"],
            "minute": now.strftime("%Y-%m-%d %H:%M"),
            "evt_time": now.strftime("%Y%m%d%H%M%S"),
        }
        logging.info(f"produce {params['evt_time']} {params}")
        db.gen_check_items(params)
        logging.info(f"produce {params['evt_time']} done")
    except:
        logging.exception("")

class Producer:
    def __init__(self):
        self.loop = None

    def start(self):
        set_signal_stop(self.stop)
        self.loop = True
        self.run()

    def stop(self):
        self.loop = False

    def run(self):
        intv = 60
        tict = time.time() // intv * intv + intv
        while self.loop:
            if tick < time.time():
                threading.Thread(target=produce).start()
                tick += intv
            time.sleep(1)


if __name__ == "__main__":
    set_logger(f"daily_check_producer.log")
    try:
        Producer().start()
    except:
        logging.exception("")


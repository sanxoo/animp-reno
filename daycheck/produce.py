import logging
import time
import threading
import datetime

import db

def produce():
    now = datetime.datetime.now()
    date = now.strftime("%Y%m%d")
    time = now.strftime("%H%M")
    weekday = now.weekday() + 1
    dayofmonth = now.day
    delta_week = now.isocalendar()[1] - (now - datetime.timedelta(days=now.day)).isocalendar()[1]
    weekofmonth = 1 if delta_week < 0 else delta_week + 1
    logging.info(f"produce {date=}, {time=}, {weekday=}, {dayofmonth=}, {weekofmonth=}")
    reserved_info = db.get_reserved_info(date, time, weekday, dayofmonth, weekofmonth)
    db.insert_check_list(reserved_info)

def main():
    intv = 60
    tick = time.time() // intv * intv + intv
    while 1:
        if tick < time.time():
            threading.Thread(target=produce).start()
            tick += intv
        time.sleep(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    #main()
    produce()


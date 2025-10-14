import logging
import time
import datetime
import enum
import argparse

from common.config import settings, set_logger
from daycheck import db, check

class Status(enum.IntEnum):
    DONE = 2
    NOK_BREAK = 3
    NOT_DEFINED = 4
    MANUAL = 5
    NOT_FOUND = 6

class Consumer:
    def __init__(self, sys_name):
        self.sys_info = db.get_system_info(sys_name)
        self.loop = None

    def start(self):
        self.loop = True
        self.run()

    def stop(self):
        self.loop = False

    def run(self):
        intv = 20
        tict = time.time() + intv
        while self.loop:
            if tick < time.time():
                try:
                    now = datetime.datetime.now()
                    self.consume(now)
                except:
                    logging.exception("")
                tick = time.time() + intv
            time.sleep(1)

    def consume(self, now):
        partition_from = (now - datetime.timedelta(days=1)).strftime("%Y%m%d000000")
        count = db.get_check_item_count(self.sys_info["sys_no"], partition_from)
        if not count: return
        self.connect()
        self.noti(count=count)
        while self.loop:
            try:
                item = db.get_check_item(self.sys_info["sys_no"], partition_from)
                if not item: break
                self.check(item)
                db.update_check_item(item)
            except:
                logging.exception("")
        self.disconn()
        self.noti()

    def noti(self, count=0):
        if count:
            pass
        else:
            pass

    def connect(self):

    def disconn(self):

    def retrieve(self, cod):

    def check(self, item):
        item["raw_pod"] = self.retrieve(item["cod"])
        if item["view_type"] == "C":
            self.compare(item)
        else:
            self.evaluate(item)
        if item["view_type"] == "V" and item["pod_result"] == "NOK":
            item["cod_state"] = Status.MANUAL

    def compare(self, item):
        std_pod = db.get_standard_pod(item)
        if std_pod:
            item["std_pod"] = std_pod["std_pod"]
            item["pod_result"], item["cmp_pod"] = check.compare(item["raw_pod"], item["std_pod"])
            item["cod_state"] = Status.DONE
        else:
            std_pod = {
            }
            db.insert_standard_pod(std_pod)
            item["std_pod"] = item["raw_pod"]
            item["pod_result"], item["cmp_pod"] = "NOK", self.format(item["raw_pod"])
            item["cod_state"] = Status.NOT_FOUND

    def evaluate(self, item):
        rule = db.get_rule()
        if rule:
            aok, txt = check.evaluate(pod, rule)
            stt = status.done
        else:
            func = check.func(...)
            if func:
                aok, txt = func(pod)
                stt = status.done
            else:
                aok, txt = False, format(pod)
                stt = status.not_defined
        return stt, aok, txt

    def format(self, raw_pod):


if __name__ == "__main__":
    pars = argparse.ArgumentParser()
    pars.add_argument("sys_name")
    args = pars.parse_args()
    set_logger(f"daycheck_consumer_{args.sys_name}.log")
    try:
        Consumer(args.sys_name).start()
    except:
        logging.exception("")


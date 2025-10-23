import logging
import time
import datetime
import enum
import traceback
import argparse

from daily_check import db, check

class RetrieveError(Exception): pass

class CodState(enum.IntEnum):
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
                    partition_from = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d000000")
                    count = db.get_check_item_count(self.sys_info["sys_no"], partition_from)
                    if count:
                        self.connect()
                        self.noti(count=count)
                        self.consume(partition_from)
                        self.disconn()
                        self.noti()
                except:
                    logging.exception("")
                tick = time.time() + intv
            time.sleep(1)

    def consume(self, partition_from):
        try:
            while self.loop:
                chk_item = db.get_check_item(self.sys_info["sys_no"], partition_from)
                if not chk_item: break
                self.check(chk_item)
                chk_item["pod_time"] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                db.put_check_item(chk_item)
        except:
            logging.exception("")

    def connect(self):

    def disconn(self):

    def retrieve(self, cod):
        raise RetreiveError()

    def noti(self, count=0):

    def check(self, chk_item):
        addition = {
            "raw_pod": "", "fmt_pod": "", "cmp_pod": "", "std_pod": "", "std_date": "",
            "pod_result": "", "reason": "", "pod_time": "",
            "cmd": chk_item["cod"].split(":")[0],
        }
        chk_item.update(addition)
        try:
            chk_item["raw_pod"] = self.retrieve(chk_item["cod"])
            if chk_item["view_type"] == "V":
                result = {
                    "fmt_pod": self.format(chk_item["raw_pod"]), "pod_result": "NOK", "cod_state": CodState.MANUAL,
                }
                chk_item.update(result)
                return
            if chk_item["view_type"] == "C":
                self.compare(chk_item)
            else:
                self.eval(chk_item)
        except Exception as e:
            reason = "pod retrieve error" if isinstance(e, RetrieveError) else "internal error"
            result = {
                "fmt_pod": self.format(traceback.format_exc()), "pod_result": "NOK", "reason": reason,
                "cod_state": CodState.DONE,
            }
            chk_item.update(result)

    def compare(self, chk_item):
        std_pod = db.get_standard_pod(chk_item)
        if std_pod:
            chk_item.update(std_pod)
            fmt_pod, res = check.compare(chk_item["raw_pod"], chk_item["std_pod"])
            result = {
                "fmt_pod": fmt_pod, "pod_result": res and "OK" or "NOK", "cod_state": CodState.DONE,
            }
            chk_item.update(result)
        else:
            std_pod = {
                "std_pod": chk_item["raw_pod"], "std_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            chk_item.update(std_pod)
            db.put_standard_pod(chk_item)
            result = {
                "fmt_pod": self.format(chk_item["raw_pod"]), "pod_result": "NOK", "cod_state": CodState.NOT_FOUND,
            }
            chk_item.update(result)

    def eval(self, chk_item):
        rule = db.get_eval_rule(chk_item)
        if rule:
            fmt_pod, res = check.evaluate(pod, rule)
            result = {
                "fmt_pod": fmt_pod, "pod_result": res and "OK" or "NOK", "cod_state": CodState.DONE,
            }
            chk_item.update(result)
        else:
            func = check.func(self.sys_info["sys_type"], chk_item["cmd"])
            if func:
                fmt_pod, res = func(chk_item["raw_pod"])
                result = {
                    "fmt_pod": fmt_pod, "pod_result": res and "OK" or "NOK", "cod_state": CodState.DONE,
                }
                chk_item.update(result)
            else:
                result = {
                    "fmt_pod": self.format(chk_item["raw_pod"]), "pod_result": "NOK", "cod_state": CodState.NOT_DEFINED,
                }
                chk_item.update(result)

    def format(self, text):
        fmt_pod = ""
        for i in text.splitlines(): fmt_pod += check.format(i, check.Color.RED)
        return fmt_pod


if __name__ == "__main__":
    pars = argparse.ArgumentParser()
    pars.add_argument("sys_name")
    args = pars.parse_args()
    set_logger(f"daycheck_consumer_{args.sys_name}.log")
    try:
        Consumer(args.sys_name).start()
    except:
        logging.exception("")


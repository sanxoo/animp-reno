import logging
import time
import enum

import check
import db

class status(enum.IntEnum):
    done = 2
    nok_break = 3
    not_defined = 4
    manual = 5
    not_found = 6

class consumer:
    def __init__(self, system_id):
        self.system_id = system_id
        self.loop = True

    def run(self):
        intv = 10
        tict = time.time() + intv
        while self.loop:
            if tick < time.time():
                try:
                    self.consume()
                except:
                    logging.exception("")
                tick = time.time() + intv
            time.sleep(1)
        self.clear()

    def stop(self):
        self.loop = False

    def consume(self):
        item = db.get_check_list_item()
        if not item: return
        self.connect()
        self.noti()
        while self.loop and item:
            cod, knd, nok, ... = item
            pod = self.retreive(cod)
            if knd == "c":
                stt, aok, txt = self.compare()
            else:
                stt, aok, txt = self.evaluate()
            if not aok and nok == "v":
                stt = status.nok_break
            db.set_check_list_item()
            if not aok:
                self.nok_break()
            item = db.get_check_list_item()
        self.noti()

    def connect(self):

    def retreive(self, pod)

    def noti(self):


    def compare(self):
        reference = db.get_reference()
        if reference:
            aok, txt = check.compare(pod, reference)
            stt = status.done
        else:
            db.set_reference(pod)
            aok, txt = False, format(pod)
            stt = status.not_found
        return stt, aok, txt

    def evaluate(self):
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

    def nok_break(self):


    def format(self, pod):


    def clear(self):
        ...


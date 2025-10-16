import logging
import time
import enum
import tomllib
import importlib
import pexpect

class ReceiveTimeout(Exception): pass

class Status(enum.IntEnum):
    UNABLE = 0
    BUSY = 1
    READY = 2
    WAITING = 3

class Session:
    def __init__(self, sys_info, custom, test=False):
        self.sys_info = sys_info
        self.custom = custom
        self.test = test
        self.conn_seq = 1
        self.cli = None
        self.passwd_pattern = None
        self.prompt_pattern = None
        self.prompt = None
        self.last_send_text = ""
        self.last_send_time = time.time()
        self.status = Status.UNABLE

    def spawn(self, command, encoding="utf-8"):
        self.cli = pexpect.spawn(command, encoding=encoding)

    def expect(self, patterns, timeout=10):
        try:
            return self.cli.expect_exact(patterns, timeout=timeout)
        except:
            if self.test:
                raise Exception(f"{self.conn_seq}|{str(patterns)}|{self.cli.before}")
            raise

    def sendline(self, text):
        self.cli.sendline(text)

    def readline(self):
        if self.passwd_pattern:
            index = self.cli.expect_exact([pexpect.TIMEOUT, "\r\n", self.prompt_pattern, self.passwd_pattern], timeout=1)
        else:
            index = self.cli.expect_exact([pexpect.TIMEOUT, "\r\n", self.prompt_pattern], timeout=1)
        if 0 < index:
            line = self.cli.before + self.cli.after
            if index == 2: self.prompt = line
            self.status = Status(index)
        else:
            line = self.cli.before
            if line: self.cli.expect(".+")
        if line: logging.debug(f"NE > {line.rstrip()}")
        return line, index

    def read_to_prompt(self, timeout=60):
        text, tick = "", time.time()
        while time.time() < tick + timeout:
            line, index = self.readline()
            if line.rstrip() == self.last_send_text:
                continue
            if index == 2:
                break
            text += line
            if index == 3:
                break
        else:
            raise ReceiveTimeout("")
        return text

    def read_pod(self, bgn_reo, end_reo, evt_reo, timeout=60):
        podo, text, tick = [], "", time.time()
        while time.time() < tick + timeout:
            line, index = self.readline()
            if line.rstrip() == self.last_send_text:
                continue
            if index == 2:
                return text if text.strip() else ""
            text += line
            if index == 3:
                return text
            if bgn_reo.match(line.rstrip()):
                podo.append(line)
                continue
            if not podo: continue
            if end_reo.match(line.rstrip()):
                podo.append(line)
                break
            if evt_reo and evt_reo.search(line) and len(podo) == 1:
                podo = []
                continue
            podo.append(line)
        else:
            raise ReceiveTimeout("")
        return "".join(podo) + "\n\n"

    def open(self):
        self.custom.open(self)
        text = self.cli.before + self.cli.after
        self.prompt = text.splitlines()[-1]
        self.status = Status.READY

    def close(self):
        try: self.custom.close(self)
        except: pass
        self.cli.close()
        self.status = Status.UNABLE

    def send(self, text):
        if self.status == Status.WAITING:
            logging.debug(f"NE < {'*' * len(text)}")
        else:
            logging.debug(f"NE < {text}")
            self.last_send_text = text
        self.custom.send(self, text)
        self.last_send_time = time.time()
        self.status = Status.BUSY

    def recv(self):
        return self.custom.recv(self)

    def is_ready(self):
        return self.status == Status.READY

    def is_waiting(self):
        return self.status == Status.WAITING

    def clean(self):
        while self.is_waiting():
            self.send("")
            _, index = self.readline()
            while index < 2:
                _, index = self.readline()
        if self.last_send_time + 60 < time.time():
            self.send("")
        line, _ = self.readline()
        while line:
            line, _ = self.readline()
        if not self.is_ready():
            self.close()
            self.open()

with open("terminal/session/__init__.toml", "rb") as toml:
    _custom_module = tomllib.load(toml)

def open(sys_info, test=False):
    sys_type = sys_info["sys_type"].lower()
    if sys_type not in _custom_module: raise Exception(f"unkown system type: {sys_type}")
    _custom = importlib.import_module(f"terminal.session.{_custom_module[sys_type]}")
    session = Session(sys_info, _custom, test)
    session.open()
    return session


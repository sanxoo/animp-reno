import logging
import time
import pexpect
import enum

system_type_to_module = {
    "wcdma_ss_msc": "wcdma_ss_msc",
}

class receive_timeout(Exception): pass

class status(enum.IntEnum):
    unable = 0
    busy = 1
    ready = 2
    waiting = 3

class session:
    def __init__(self, module, system_info):
        self.handler = module.handler(self)
        self.system_info = system_info
        self.cli = None
        self.passwd_prompt = None
        self.prompt = None
        self.prompt_line = None
        self.last_send_text = ""
        self.last_send_time = time.time()
        self.status = status.unable

    def spawn(self, command):
        self.cli = pexpect.spawn(command)

    def expect(self, patterns, timeout=10):
        return self.cli.expect_exact(patterns, timeout=timeout)

    def sendline(self, text):
        self.cli.sendline(text)

    def readline(self):
        if self.passwd_prompt:
            index = self.cli.expect_exact([pexpect.TIMEOUT, "\r\n", self.prompt, self.passwd_prompt], timeout=1)
        else:
            index = self.cli.expect_exact([pexpect.TIMEOUT, "\r\n", self.prompt], timeout=1)
        if 0 < index:
            line = (self.cli.before + self.cli.after).decode()
            if index == 2: self.prompt_line = line
            self.status = status(index)
        else:
            line = (self.cli.before).decode()
            if line: self.cli.expect(".+")
        if line: logging.debug(f"NE > {line.rstrip()}")
        return line, index

    def read2prompt(self, timeout=60):
        text, tick = "", time.time()
        while 1:
            if tick + timeout < time.time(): raise receive_timeout("")
            line, index = self.readline()
            if index == 2: break
            text += line
            if index == 3: break
        return text

    def open(self):
        self.handler.open()
        text = (self.cli.before + self.cli.after).decode()
        self.prompt_line = text.splitlines()[-1]
        self.status = status.ready

    def close(self):
        self.handler.close()
        self.cli.close()
        self.status = status.unable

    def send(self, text):
        if self.status == status.waiting:
            logging.debug(f"NE < {'*' * len(text)}")
        else:
            logging.debug(f"NE < {text}")
            self.last_send_text = text
        self.handler.send(text)
        self.last_send_time = time.time()
        self.status = status.busy

    def recv(self):
        return self.handler.recv()

    def clear(self):
        while self.status == status.waiting:
            self.send("")
            _, index = self.readline()
            while index < 2:
                _, index = self.readline()
        if self.last_send_time + 60 < time.time():
            self.send("")
        line, _ = self.readline()
        while line:
            line, _ = self.readline()
        if self.status != status.ready:
            self.close()
            self.open()


def open(system_info):
    system_type = system_info["type"].lower()
    if system_type not in system_type_to_module: raise Exception(f"unkown system type: {system_type}")
    import importlib
    module = importlib.import_module(f"session.{system_type_to_module[system_type]}")
    sess = session(module, system_info)
    sess.open()
    return sess


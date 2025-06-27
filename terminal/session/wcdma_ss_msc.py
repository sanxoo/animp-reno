import logging
import time

import session

class handler:
    def __init__(self, session):
        self.session = session

    def open(self):
        conn = self.session.system_info["conn"]
        host = conn[0]["host"]
        port = conn[0]["port"]
        user = conn[0]["user"]
        pswd = conn[0]["pswd"]
        prpt = conn[0]["prpt"]

        command = f"ssh {user}@{host} -p {port}"
        logging.info(command)
        self.session.spawn(command)
        self.session.expect("password: ")
        self.session.sendline(pswd)
        self.session.expect(prpt)

        host = conn[1]["host"]
        port = conn[1]["port"]
        user = conn[1]["user"]
        pswd = conn[1]["pswd"]
        prpt = conn[1]["prpt"]

        command = f"ssh {user}@{host} -p {port}"
        logging.info(command)
        self.session.sendline(command)
        index = self.session.expect(["password: ", "(yes/no/[fingerprint])? "])
        if index == 1:
            self.session.sendline("yes")
            self.session.expect("password: ")
        self.session.sendline(pswd)
        self.session.expect(prpt)

        self.session.passwd_prompt = "password for sanxoo: "
        self.session.prompt = prpt

    def close(self):
        self.session.sendline("exit")
        self.session.sendline("exit")

    def send(self, text):
        self.session.sendline(text)

    def recv(self):
        return self.session.read2prompt()


import logging
import time
import threading
import socket
import re

class mux(threading.Thread):
    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server = server
        self.urgent_que = []
        self.que = []
        self.socket = None
        self.socket_file = None
        self.last_interact = None
        self.begin_pattern = re.compile("<BEGIN>.*</BEGIN>")
        self.end_pattern = re.compile("<END>.*</END>")
        self.passwd_pattern = re.compile(".*<PASSWORD/>")
        self.loop = True

    def run(self):
        try:
            self.connect(self)
            self.last_interact = time.time()
            while self.loop:
                if not self.urgent_que:
                    if not self.que:
                        if self.last_interact + 600 < time.time():
                            self.send("")
                            self.last_interact = time.time()
                        time.sleep(1)
                        continue
                    client_id, pri, passwd, cmd = self.que.pop(0)
                else:
                    client_id, pri, passwd, cmd = self.urgent_que.pop(0)
                self.server.log(client_id, pri, cmd)
                self.send(cmd)
                self.recv(client_id, pri, passwd)
                self.last_interact = time.time()
        except:
            logging.exception("")
        finally:
            self.clear()

    def stop(self):
        self.loop = False

    def push(self, client_id, pri, passwd, cmd):
        if pri != "1":
            self.urgent_que.append((client_id, pri, passwd, cmd))
        else:
            self.que.append((client_id, pri, passwd, cmd))

    def connect(self):
        self.socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 0x1f0000)
        self.socket.connect(())
        self.socket_file = self.socket.makefile(encoding="euc-kr")
        line = f"".encode("euc-kr")
        self.socket.sendall(line)
        self.socket.settimeout(10)
        line = self.socket_file.readline()
        if not line or not line.endswith("CONNECTED\n"): raise Exception(f"fail to read 'connect'")
        self.socket.settimeout(1)

    def send(self, cmd):
        logging.debug(f"MUX < {cmd}")
        line = (cmd + "\n").encode("euc-kr")
        self.socket.sendall(line)

    def recv(self, client_id, pri, passwd):
        timeout = time.time() + 900
        pod = ""
        while self.loop:
            if timeout < time.time():
                pod = ""
                break
            try:
                line = self.socket_file.readline()
            except socket.timeout:
                continue
            line_str = line.rstrip()
            logging.debug(f"MUX > {line_str}")
            if self.begin_pattern.match(line_str):
                pod = ""
                continue
            if self.end_pattern.match(line_str):
                break
            if self.passwd_pattern.match(line_str)
                self.send(passwd)
                continue
            pod += line
        self.server.post(client_id, pri, pod)

    def clear(self):
        logging.info(f"clear")
        try:
            self.send("exit")
            self.socket_file.close()
            self.socket.close()
        except:
            pass


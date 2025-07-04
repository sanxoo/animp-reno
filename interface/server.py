import logging
import time
import socket
import select
import uuid
import threading

import mux
import db

class server:
    def __init__(self, system_id):
        self.system_id = system_id
        self.system_info = db.get_system_info(system_id)
        self.mux = mux.mux(self)
        self.bind_socket = None
        self.handlers = {}
        self.loop = True

    def run(self):
        try:
            self.mux.start()
            mux_start_time = time.time()
            mux_restart_count = 0
            self.bind()
            while self.loop:
                sockets, _, _ = select.select([self.bind_socket], [], [], 1)
                if self.bind_socket in sockets:
                    socket, (ip, port) = self.bind_socket.accept()
                    client_id = str(uuid.uuid4())
                    logging.info(f"accept {ip}:{port} {client_id}")
                    self.handlers[client_id] = handler(self.system_id, self.mux, client_id, socket)
                    self.handlers[client_id].start()
                else:
                    if not self.mux.is_alive():
                        if 2 < mux_restart_count: raise Exception(f"fail to start mux, {mux_restart_count=}")
                        self.mux.start()
                        mux_start_time = time.time()
                        mux_restart_count += 1
                    else:
                        if 0 < mux_restart_count and mux_start_time + 1200 < time.time():
                            mux_restart_count = 0
                    for client_id in self.handlers.keys():
                        if self.handlers[client_id].is_alive(): continue
                        logging.info(f"delete {client_id}")
                        del self.handlers[client_id]
        except:
            logging.exception("")
        finally:
            self.clear()

    def stop(self):
        self.loop = False

    def log(self, client_id, pri, cmd):
        if client_id in self.handlers: self.handlers[client_id].log(pri, cmd)

    def post(self, client_id, pri, pod):
        if client_id in self.handlers: self.handlers[client_id].post(pri, pod)

    def bind(self):
        self.bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = self.system_info["port"]
        logging.info(f"bind {port}")
        self.bind_socket.bind(("", int(port)))
        self.bind_socket.listen(socket.SOMAXCONN)

    def clear(self):
        logging.info(f"clear")
        for handler in self.handlers.values(): handler.stop()
        for handler in self.handlers.values(): handler.join()
        if self.bind_socket: self.bind_socket.close()
        if self.mux:
            self.mux.stop()
            self.mux.join()


class handler(threading.Thread):
    def __init__(self, system_id, mux, client_id, socket):
        threading.Thread.__init__(self)
        self.system_id = system_id
        self.mux = mux
        self.client_id = client_id
        self.socket = socket
        self.nms_no = None
        self.nms_id = None
        self.phone_no = None
        self.free = None
        self.system_no = None
        self.last_cmd = None
        self.last_cmd_time = None
        self.loop = True

    def run(self):
        try:
            self.socket.settimeout(2)
            self.prepare()
            hb_timeout = time.time() + 1200
            while self.loop:
                if hb_timeout < time.time(): raise Exception(f"heart beat timeout")
                kind, text = self.recv()
                if not kind: continue
                hb_timeout = time.time() + 1200
                if kind == "03":
                    break
                if kind == "04":
                    cmd = text[34:].strip()
                    if not self.free:
                        real_cmd = cmd.repalce("/usr/local/bin/mmc", "").strip()
                        for word in []:
                            if real_cmd.startswith(word): break
                        else:
                            self.send("05", text[0] + "20" + " " * 7)
                            continue
                    if cmd == self.last_cmd and time.time() - self.last_cmd_time < 3.0:
                        self.send("05", text[0] + "23" + " " * 7)
                    else:
                        passwd = base64.b64decode(text[10:34])
                        self.mux.push(self.client_id, text[0], passwd, cmd)
                    self.last_cmd = cmd
                    self.last_cmd_time = time.time()
                if kind == "06":
                    self.send("07", "")
        except:
            logging.exception("")
            if self.nms_no: self.noti()
        finally:
            self.clear()

    def stop(self):
        self.loop = False

    def log(self, client_id, pri, cmd):
        ...

    def post(self, pri, pod):
        try:
            text = pri + "10" + " " * 7 + pod if pod else pri + "22" + " " * 7
            self.send("05", text)
        except:
            logging.exception("")
            self.stop()

    def prepare(self):
        kind, text = self.recv()
        if kind != "01": raise Exception(f"invalid packet kind {kind}")
        system_id = text[:20].rstrip()
        if system_id != self.system_id: raise Exception(f"invalid system id {system_id}")
        nms_id = text[20:44]
        passwd, nms_no, phone_no, free, system_no = db.get_nms_info(nms_id, system_id)
        if passwd != text[44:]: raise Exception(f"invalid password")
        db.log_nms_login(nms_no, "ok")
        self.nms_no = nms_no
        self.nms_id = nms_id
        self.phone_no = phone_no
        self.free = free.lower() == "t"
        self.system_no = system_no
        self.send("02", text[:20])

    def recv(self):
        try:
            head = socket.recv(12).decode()
        except socket.timeout:
            return "", ""
        kind = head[:2]
        size = int(head[2:]) - 12
        text = socket.recv(size).decode() if 0 < size else ""
        logging.debug(f"NMS > {head}{text}")
        return kind, text

    def send(self, kind, text):
        pack = "%s%010d%s" % (kind, len(text) + 12, text)
        logging.debug(f"NMS < {pack}")
        pack = pack.encode()
        sent = 0
        while sent < len(pack): sent += socket.send(pack[sent:])

    def noti(self):
        ...

    def clear(self):
        try:
            self.send("03", self.system_id + " " * (20 - len(self.system_id)))
            self.socket.close()
        except:
            pass


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        sys.stderr.write(f"\nusage: {sys.argv[0]} system_id\n\n")
        sys.exit()
    logging.basicConfig(level=logging.DEBUG)
    inst = server(*sys.argv[1:])
    inst.run()


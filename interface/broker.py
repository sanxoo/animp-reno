import logging
import time
import socket
import select

import config
import db

class broker:
    def __init__(self):
        self.bind_socket = None
        self.loop = True

    def run(self):
        try:
            self.bind()
            while self.loop:
                sockets, _, _ = select.select([self.bind_socket], [], [], 1)
                if self.bind_socket in sockets:
                    socket, (ip, port) = self.bind_socket.accept()
                    logging.info(f"accept {ip}:{port}")
                    self.handle(socket)
        except:
            logging.exception("")
        finally:
            self.clear()

    def stop(self):
        self.loop = False

    def bind(self):
        self.bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = config.settings["broker"]["port"]
        logging.info(f"bind {port}")
        self.bind_socket.bind(("", int(port)))
        self.bind_socket.listen(socket.SOMAXCONN)

    def handle(self, socket):
        now = time.strftime("%Y%m%d%H%M%S")
        try:
            socket.settimeout(2)
            kind, text = self.recv(socket)
            if kind != "08": raise Exception(f"invalid packet kind {kind}")
            nms_id = text[:24]
            passwd, nms_no = db.get_nms_info(nms_id)
            if passwd != text[24:]:
                desc = "authetication error"
                text = now + "20"
            else:
                desc = "ok"
                host = config.settings["broker"]["host"] 
                list = [f"{system_id}|^|{host}|^|{port}" for system_id, port in db.get_nms_system_list(nms_no)]
                text = now + "10" + "|^^|".join(list)
            db.log_nms_login(nms_no, desc)
            self.send(socket, "09", text)
        except:
            logging.exception("")
            self.send(socket, "09", now + "22")
        finally:
            socket.close()

    def recv(self, socket):
        head = socket.recv(12).decode()
        kind = head[:2]
        size = int(head[2:]) - 12
        text = socket.recv(size).decode() if 0 < size else ""
        logging.debug(f"NMS > {head}{text}")
        return kind, text

    def send(self, socket, kind, text):
        pack = "%s%010d%s" % (kind, len(text) + 12, text)
        logging.debug(f"NMS < {pack}")
        pack = pack.encode()
        sent = 0
        while sent < len(pack): sent += socket.send(pack[sent:])

    def clear(self):
        logging.info(f"clear")
        if self.bind_socket: self.bind_socket.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    inst = broker()
    inst.run()


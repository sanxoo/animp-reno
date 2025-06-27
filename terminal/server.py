import logging
import socket
import select
import uuid

import mux
import db

class server:
    def __init__(self, system_info):
        self.system_info = system_info
        self.mux = mux.mux(self)
        self.bind_socket = None
        self.clients = {}
        self.loop = True

    def run(self):
        try:
            self.mux.start()
            self.bind()
            while self.loop:
                sockets, _, _ = select.select([self.bind_socket] + [i[0] for i in self.clients.values()], [], [], 1)
                for socket in sockets:
                    if socket == self.bind_socket:
                        self.accept()
                    else:
                        self.recv(socket)
        except:
            logging.exception("")
        finally:
            self.clear()

    def stop(self):
        self.loop = False

    def bind(self):
        self.bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = self.system_info["port"]
        logging.info(f"bind {port}")
        self.bind_socket.bind(("", int(port)))
        self.bind_socket.listen(socket.SOMAXCONN)

    def accept(self):
        socket, address = self.bind_socket.accept()
        logging.info(f"accept {address}")
        try:
            socket.settimeout(3)
            line = socket.makefile().readline()
            user, passwd, ip = line.strip().split("|^|")
        except:
            logging.exception("")
            socket.close()
            return
        client_id = str(uuid.uuid4())
        logging.info(f"client {client_id}, {user}, {ip}")
        self.clients[client_id] = [socket, user, ip]
        self.send(client_id, "\nWELCOME\n\n")
        self.send(client_id, self.mux.prompt())

    def recv(self, socket):
        for client_id in self.clients:
            if self.clients[client_id][0] == socket: break
        else:
            return
        try:
            line = socket.makefile().readline()
            if not line: raise Exception("client socket closed")
            text = line.strip()
            logging.debug(f"UI > {text}")
            if text.startswith("exit"): raise Exception("client exited")
            self.mux.push(client_id, text)
        except:
            logging.exception("")
            self.drop(client_id)

    def send(self, client_id, text):
        if client_id not in self.clients: return
        for line in text.splitlines():
            logging.debug(f"UI < {line}")
        try:
            socket = self.clients[client_id][0]
            text = text.encode()
            sent = 0
            while sent < len(text):
                sent += socket.send(text[sent:])
        except:
            logging.exception("")
            self.drop(client_id)

    def hist(self, client_id, text, hist_timeout=0):
        socket, user, ip = self.clients[client_id]
        if hist_timeout:
            db.hist_timeout(user, ip, text)
        else:
            db.hist_cammand(user, ip, text)

    def drop(self, client_id):
        socket, user, ip = self.clients[client_id]
        logging.info(f"drop {client_id}, {user}, {ip}")
        socket.close()
        del self.clients[client_id]

    def clear(self):
        for client_id in list(self.clients.keys()): self.drop(client_id)
        if self.bind_socket: self.bind_socket.close()
        if self.mux:
            self.mux.stop()
            self.mux.join()


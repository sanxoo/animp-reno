import logging
import socket
import select
import uuid
import argparse

from collections import namedtuple

from lib.common import set_logger, set_signal_stop
from bin.terminal import db, mux

client = namedtuple("client", ["socket", "user_id", "user_ip"])

class Server:
    def __init__(self, sys_name, svc_type):
        self.sys_info = db.get_system_info(sys_name, svc_type)
        self.mux = mux.Mux(self)
        self.bind_socket = None
        self.clients = {}
        self.loop = None

    def start(self):
        set_signal_stop(self.stop)
        self.loop = True
        self.run()

    def stop(self):
        self.loop = False

    def run(self):
        try:
            self.mux.start()
            self.listen()
            while self.loop:
                sockets, _, _ = select.select([self.bind_socket] + [i.socket for i in self.clients.values()], [], [], 1)
                for socket in sockets:
                    if socket == self.bind_socket:
                        self.accept()
                    else:
                        self.recv(socket)
        except:
            logging.exception("")
        finally:
            for client_id in list(self.clients.keys()): self.drop(client_id)
            if self.bind_socket: self.bind_socket.close()
            if self.mux.is_alive(): self.mux.stop()

    def listen(self):
        self.bind_socket = socket.create_server(("", self.sys_info["port"]), reuse_port=True)
        logging.info(f"listen {self.sys_info['port']}")

    def accept(self):
        socket, (ip, port) = self.bind_socket.accept()
        logging.info(f"accept {ip}:{port}")
        try:
            socket.settimeout(3)
            line = socket.makefile(encoding="euc-kr").readline()
            user_id, user_ip = line.strip().split("|^|")
        except:
            logging.exception("")
            socket.sendall("CONNECTION REFUSED BY ANIMP\n".encode("euc-kr"))
            socket.close()
            return
        client_id = uuid.uuid4().hex
        logging.info(f"client {client_id}, {user_id}, {user_ip}")
        self.clients[client_id] = client(socket, user_id, user_ip)
        self.send(client_id, "CONNECTED\n")
        self.send(client_id, self.mux.prompt())

    def recv(self, socket):
        for client_id in self.clients:
            if self.clients[client_id].socket == socket: break
        else:
            return
        try:
            line = socket.makefile(encoding="euc-kr").readline()
            if not line: raise Exception("client socket closed")
            text = line.strip()
            logging.debug(f"UI > {text}")
            if text.lower().startswith(("exit", "quit", "logout", "log-out")): raise Exception("client exited")
            self.mux.push(client_id, text)
        except:
            logging.exception("")
            self.drop(client_id)

    def send(self, client_id, text):
        if client_id not in self.clients: return
        for line in text.splitlines():
            logging.debug(f"UI < {line}")
        try:
            socket = self.clients[client_id].socket
            text = text.encode("euc-kr")
            sent = 0
            while sent < len(text):
                sent += socket.send(text[sent:])
        except:
            logging.exception("")
            self.drop(client_id)

    def drop(self, client_id):
        logging.info(f"drop client {client_id}")
        self.clients[client_id].socket.close()
        del self.clients[client_id]

    def hist(self, client_id, cod, event="execute"):
        socket, user_id, user_ip = self.clients[client_id]
        if event == "execute":
            pass
        if event == "timeout":
            pass


if __name__ == "__main__":
    pars = argparse.ArgumentParser()
    pars.add_argument("sys_name")
    pars.add_argument("svc_type", choices=["terminal", "daycheck"], type=str.lower)
    args = pars.parse_args()
    try:
        set_logger(f"terminal_{args.sys_name}_{args.svc_type}.log")
        server = Server(args.sys_name, args.svc_type)
        server.start()
    except:
        logging.exception("")


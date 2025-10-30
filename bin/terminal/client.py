import argparse
import socket
import select

from bin.terminal import db
from lib import ace

pars = argparse.ArgumentParser()
pars.add_argument("sys_name")
args = pars.parse_args()
info = db.get_system_info(args.sys_name, "terminal")

sock = socket.create_connection(ace.get_addr_by_port(info["port"]))

def send(text):
    sock.sendall((text + "\n").encode("euc-kr"))

def recv():
    text = ""
    while 1:
        ifds, _, _ = select.select([sock], [], [], 1)
        if sock in ifds:
            byte = sock.recv(1024)
            if not byte: break
            text = text + byte.decode("euc-kr")
        else:
            break
    return text

send("O127001|^|127.0.0.1")
text = recv()
while text:
    print(text)
    send(input())
    text = recv()

sock.close()


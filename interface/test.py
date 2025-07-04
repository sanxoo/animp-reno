import socket
import config

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("localhost", config.settings["broker"]["port"]))
text = "*" * 24 + "password"
pack = "%s%010d%s" % ("08", len(text) + 12, text)
pack = pack.encode()
sock.sendall(pack)
head = sock.recv(12).decode()
size = int(head[2:]) - 12
text = sock.recv(size).decode()
print(head + text)
sock.close()


import logging
import time
import threading

import session

class waiting_timeout(Exception): pass

class mux(threading.Thread):
    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server = server
        self.que = []
        self.session = None
        self.loop = True

    def run(self):
        try:
            self.session = session.open(self.server.system_info)
            while self.loop:
                if not self.que:
                    self.session.clear()
                else:
                    self.pop()
        except:
            logging.exception("")
        finally:
            if self.session: self.session.close()

    def start(self):
        threading.Thread.start(self)
        while not self.session: time.sleep(1)

    def stop(self):
        self.loop = False

    def prompt(self):
        return self.session.prompt_line

    def push(self, client_id, text):
        self.que.append((client_id, text))

    def pop(self):
        client_id, text = self.que.pop(0)
        self.session.send(text)
        self.server.send(client_id, "\nSTART\n\n")
        self.server.hist(client_id, text)
        try:
            while self.session.status != session.status.ready:
                text = self.session.recv()
                self.server.send(client_id, text)
                if self.session.status == session.status.waiting:
                    self.wait(client_id)
        except session.receive_timeout:
            self.server.send(client_id, "\n\nRECEIVE TIMEOUT\n\n")
            self.server.hist(client_id, text, 1)
            self.session.clear()
        except waiting_timeout:
            self.server.send(client_id, "\n\nWAITING TIMEOUT\n\n")
            self.session.clear()
        self.server.send(client_id, "\nEND\n\n")
        self.server.send(client_id, self.prompt())

    def wait(self, client_id):
        now = time.time()
        while time.time() < now + 10:
            time.sleep(1)
            for i, text in self.que:
                if i == client_id: break
            else:
                continue
            self.que.remove((i, text))
            self.session.send(text)
            break
        else:
            raise waiting_timeout("")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import sys
    system_info = {
        "type": "wcdma_ss_msc", "id": "msc",
        "conn": [
            {"host": "192.168.101.224", "port": 22, "user": "sanxoo", "pswd": "tjddms00))", "prpt": "\x1b[0m$ "},
            {"host": "192.168.101.224", "port": 22, "user": "sanxoo", "pswd": "tjddms00))", "prpt": "\x1b[0m$ "},
        ],
        "port": 2000
    }

    class console:
        def __init__(self):
            self.system_info = system_info
            self.mux = None
        def send(self, i, text):
            sys.stdout.write(text)
            sys.stdout.flush()
        def hist(self, i, text):
            pass
        def run(self):
            self.mux = mux(self)
            self.mux.start()
            self.send(1, "\nWELCOME, ENTER 'exit' TO QUIT.\n\n")
            self.send(1, self.mux.prompt())
            while 1:
                try:
                    text = input()
                    if text.lower() == "exit":
                        self.send(1, "\n")
                        break
                    self.mux.push(1, text)
                except:
                    self.send(1, "\n\n")
                    break
            self.mux.stop()
            self.mux.join()

    console().run()


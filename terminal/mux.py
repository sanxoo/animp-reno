import logging
import time
import threading

from terminal import session

class WaitingTimeout(Exception): pass

class Mux(threading.Thread):
    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server = server
        self.que = []
        self.session = None
        self.loop = None

    def start(self):
        self.session = session.open(self.server.sys_info)
        self.loop = True
        threading.Thread.start(self)

    def stop(self):
        self.loop = False
        self.join()

    def run(self):
        try:
            while self.loop:
                if not self.que:
                    self.session.clean()
                else:
                    self.pop()
        except:
            logging.exception("")
        finally:
            self.session.close()

    def prompt(self):
        return self.session.prompt

    def push(self, client_id, cod):
        self.que.append((client_id, cod))

    def pop(self):
        client_id, cod = self.que.pop(0)
        self.session.send(cod)
        self.server.send(client_id, f"<BEGIN>{cod}</BEGIN>\n")
        self.server.hist(client_id, cod)
        try:
            while not self.session.is_ready():
                pod = self.session.recv()
                if pod: self.server.send(client_id, pod)
                if self.session.is_waiting():
                    self.server.send(client_id, "<PASSWORD/>\n")
                    self.wait(client_id)
        except session.ReceiveTimeout:
            self.server.send(client_id, "RESPONSE TIMEOUT!\n")
            self.server.hist(client_id, cod, "timeout")
            self.session.clean()
        except WaitingTimeout:
            self.server.send(client_id, "TIMEOUT!\n")
            self.session.clean()
        self.server.send(client_id, f"<END>{cod}</END>\n")
        self.server.send(client_id, self.prompt())

    def wait(self, client_id):
        now = time.time()
        while time.time() < now + 10:
            time.sleep(1)
            for i, pwd in reversed(self.que):
                if i == client_id: break
            else:
                continue
            self.que.remove((i, pwd))
            self.session.send(pwd)
            break
        else:
            raise WaitingTimeout("")


if __name__ == "__main__":
    import argparse
    pars = argparse.ArgumentParser()
    pars.add_argument("sys_name")
    pars.add_argument("svc_type", choices=["terminal", "daycheck"], type=str.lower)
    args = pars.parse_args()

    logging.basicConfig(
        format="%(asctime)s %(levelno)s %(filename)s:%(lineno)03d - %(message)s",
        level=logging.DEBUG,
    )

    from terminal import db
    class server:
        def __init__(self):
            self.sys_info = db.get_test_system_info()   #db.get_system_info(args.sys_name, args.svc_type)
        def send(self, i, text):
            print(text, end="", flush=True)
        def hist(self, i, cod, event="execute"):
            pass
        def run(self):
            self.mux = Mux(self)
            self.mux.start()
            self.send(1, "\nWELCOME, ENTER 'exit' TO QUIT.\n\n")
            self.send(1, self.mux.prompt())
            while 1:
                try:
                    cod = input()
                    if cod.lower() == "exit":
                        self.send(1, "\n")
                        break
                    self.mux.push(1, cod)
                except:
                    self.send(1, "\n\n")
                    break
            self.mux.stop()
            self.mux.join()
    server().run()


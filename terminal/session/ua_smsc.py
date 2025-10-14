import logging
import re

from terminal.session import Status, ReceiveTimeout

def open(session):
    seq = session.sys_info["seqs"]["1"]
    if seq["port"] == "22":
        cmd = f"ssh {seq['id']}@{seq['ip']} -p {seq['port']}"
        logging.info(f"1: {cmd}")
        session.spawn(cmd, encoding="euckr")
        index = session.expect(["password: ", "(yes/no/[fingerprint])? "])
        if index == 1:
            session.sendline("yes")
            session.expect("password: ")
    else:
        cmd = f"telnet {seq['ip']} {seq['port']}"
        logging.info(f"1: {cmd}")
        session.spawn(cmd, encoding="euckr")
        session.expect("login: ")
        session.sendline(seq["id"])
        session.expect("Password: ")
    session.sendline(seq["pw"])
    session.expect(seq["prompt"])

    seq = session.sys_info["seqs"]["2"]
    cmd = f"telnet {seq['ip']} {seq['port']}"
    logging.info(f"2: {cmd}")
    session.sendline(cmd)
    session.expect("login: ")
    session.sendline(seq["id"])
    session.expect("Password: ")
    session.sendline(seq["pw"])
    session.expect(seq["prompt"])

    seq = session.sys_info["seqs"]["3"]
    cmd = f"rmi"
    logging.info(f"3: {cmd}")
    session.sendline(cmd)
    session.expect("LOGIN: ")
    session.sendline(seq["id"])
    session.expect("PASSWOED: ")
    session.sendline(seq["pw"])
    session.expect(seq["prompt"])

    session.passwd_pattern = None
    session.prompt_pattern = seq["prompt"]

def close(session):
    session.sendline("exit")
    session.sendline("exit")
    session.sendline("exit")

def send(session, text):
    session.sendline(text)

_bgn_reo = re.compile("\s*\S+\s+\d\d\d\d-\d\d-\d\d\s+\d\d:\d\d:\d\d\s+\S+\s+\S+")
_end_reo = re.compile("\s*COMPLETED|\s*CONTINUE")
_evt_reo = re.compile("[ \*]+[FAST]\d\d\d\d ")
_pwd_reo = re.compile("PASSWORD: |>> INPUT ")

def recv(session):
    podo, text, tick = [], "", time.time()
    while time.time() < tick + 60:
        line, index = session.readline()
        if line.rstrip() == session.last_send_text:
            continue
        if index == 2:
            return text if text.strip() else ""
        text += line
        if _pwd_reo.search(line):
            session.status = Status.WAITING
            return text
        if _bgn_reo.match(line.rstrip()):
            podo.append(line)
            continue
        if not podo: continue
        if _end_reo.match(line.rstrip()):
            podo.append(line)
            break
        if _evt_reo.search(line) and len(podo) == 1:
            podo = []
            continue
        podo.append(line)
    else:
        raise ReceiveTimeout("")
    return "".join(podo) + "\n\n"


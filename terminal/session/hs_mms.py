import logging
import re

from terminal.session import Status, ReceiveTimeout

def open(session):
    seq = session.sys_info["seqs"]["1"]
    if seq["port"] == "22":
        cmd = f"ssh {seq['id']}@{seq['ip']} -p {seq['port']}"
        logging.info(f"1: {cmd}")
        session.spawn(cmd)
        index = session.expect(["password: ", "(yes/no/[fingerprint])? "])
        if index == 1:
            session.sendline("yes")
            session.expect("password: ")
    else:
        cmd = f"telnet {seq['ip']} {seq['port']}"
        logging.info(f"1: {cmd}")
        session.spawn(cmd)
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

    session.passwd_pattern = None
    session.prompt_pattern = seq["prompt"]

def close(session):
    session.sendline("exit")
    session.sendline("exit")

def send(session, text):
    session.sendline(text)

_bgn_reo = re.compile("\S+\s+\d\d\d\d-\d\d-\d\d\s+\d\d:\d\d:\d\d\s+\S+")
_end_reo = re.compile(";")
_pwd_reo = re.compile("Enter password")

def recv(session):
    podo, text, tick = [], "", time.time()
    while time.time() < tick + 60:
        line, index = session.readline()
        if line.rstrip() == session.last_send_text:
            continue
        if index == 2 and "PARAM" not in line:
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
        podo.append(line)
    else:
        raise ReceiveTimeout("")
    return "".join(podo) + "\n\n"


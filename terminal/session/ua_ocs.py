import logging
import re

def open(session):
    seq = session.sys_info["seqs"]["2"]
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

    seq = session.sys_info["seqs"]["3"]
    cmd = f"rmi"
    logging.info(f"2: {cmd}")
    session.sendline(cmd)
    session.expect("LOGIN: ")
    session.sendline(seq["id"])
    session.expect("PASSWOED: ")
    session.sendline(seq["pw"])
    session.expect(seq["prompt"])

    session.passwd_pattern = "PASSWORD: "
    session.prompt_pattern = seq["prompt"]

def close(session):
    session.sendline("exit")
    session.sendline("exit")

def send(session, text):
    session.sendline(text)

_bgn_reo = re.compile("\s*\S+\s+\d\d\d\d-\d\d-\d\d\s+\d\d:\d\d:\d\d\s+\S+\s+\S+")
_end_reo = re.compile("\s*COMPLETED|\s*CONTINUE")
_evt_reo = re.compile("[ \*]+[FAST]\d\d\d\d ")

def recv(session):
    return session.read_pod(_bgn_reo, _end_reo, _evt_reo)


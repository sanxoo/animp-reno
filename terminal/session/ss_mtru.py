import logging
import re

def open(session):
    seq = session.sys_info["seqs"]["1"]
    session.conn_seq = 1
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
    session.conn_seq = 2
    cmd = f"telnet {seq['ip']} {seq['port']}"
    logging.info(f"2: {cmd}")
    session.sendline(cmd)
    session.expect("USERNAME : ")
    session.sendline(seq["id"])
    session.expect("PASSWORD : ")
    session.sendline(seq["pw"])
    session.expect(seq["prompt"])

    session.sendline("INH-MSG:TYPE=STATUS,ID=1100;")
    session.expect(seq["prompt"])
    session.sendline("INH-MSG:TYPE=STATUS,ID=1102;")
    session.expect(seq["prompt"])
    session.sendline("INH-MSG:TYPE=FAULT,ID=2000;")
    session.expect(seq["prompt"])

    session.passwd_pattern = "PASSWORD : "
    session.prompt_pattern = seq["prompt"]

def close(session):
    session.sendline("EXIT;")
    session.sendline("exit")

def send(session, text):
    session.sendline(text)

_bgn_reo = re.compile("\s+\S+\s+\d\d\d\d-\d\d-\d\d\s+\d\d:\d\d:\d\d")
_end_reo = re.compile(";")
_evt_reo = re.compile("[FS]\s+\d\d\d\d ")

def recv(session):
    if session.last_send_text == "RTRV-HIST;":
        return session.read_to_prompt()
    if session.last_send_text.endswith("?"):
        text = session.read_to_prompt()
        session.sendline("")
        session.clean()
        return text

    return session.read_pod(_bgn_reo, _end_reo, _evt_reo)


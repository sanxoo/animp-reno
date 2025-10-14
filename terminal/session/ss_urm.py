import logging
import re

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

    session.sendline("setenv LANG C")
    session.expect(seq["prompt"])

    session.passwd_pattern = None
    session.prompt_pattern = seq["prompt"]

def close(session):
    session.sendline("exit")

def send(session, text):
    session.sendline(text)

_bgn_reo = re.compile("\s+\S+\s+\d\d\d\d-\d\d-\d\d\s+\d\d:\d\d:\d\d\s+\S+")
_end_reo = re.compile("\s+COMPLETED|\s+CONTINUE")
_evt_reo = re.compile("[ \*]+[FAST]\d\d\d\d ")

def recv(session):
    if not session.last_send_texti.startswith("ucmdx"):
        return session.read_to_prompt()

    return session.read_pod(_bgn_reo, _end_reo, _evt_reo)


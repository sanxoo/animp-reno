import logging
import re

def open(session):
    seq = session.sys_info["seqs"]["1"]
    session.conn_seq = 1
    cmd = f"ssh {seq['id']}@{seq['ip']} -p {seq['port']}"
    logging.debug(f"1: {cmd}")
    session.spawn(cmd, encoding="euckr")
    index = session.expect(["password: ", "(yes/no/[fingerprint])? "])
    if index == 1:
        session.sendline("yes")
        session.expect("password: ")
    session.sendline(seq["pw"])
    session.expect(seq["prompt"])

    seq = session.sys_info["seqs"]["2"]
    session.conn_seq = 2
    cmd = f"ssh {seq['id']}@{seq['ip']} -p {seq['port']}"
    logging.debug(f"2: {cmd}")
    session.sendline(cmd)
    session.expect("password: ")
    session.sendline(seq["pw"])
    session.expect(seq["prompt"])

    session.sendline("cd /apps/pkg/sw/bin")
    session.expect(seq["prompt"])

    seq = session.sys_info["seqs"]["3"]
    session.conn_seq = 3
    cmd = f"./CLI"
    logging.debug(f"3: {cmd}")
    session.sendline(cmd)
    session.expect("USERNAME : ")
    session.sendline(seq["id"])
    session.expect("PASSWORD : ")
    session.sendline(seq["pw"])
    session.expect(seq["prompt"])

    session.passwd_pattern = "PASSWORD : "
    session.prompt_pattern = seq["prompt"]

def close(session):
    session.sendline("EXIT;")
    session.sendline("exit")
    session.sendline("exit")

def send(session, text):
    session.sendline(text)

_bgn_reo = re.compile("\s+\S+\s+\d\d\d\d-\d\d-\d\d\s+\S+\s+\d\d:\d\d:\d\d")
_end_reo = re.compile(";")
_evt_reo = re.compile("[ \*]+[FAST]\d\d\d\d ")

def recv(session):
    if session.last_send_text == "RTRV-HIST;":
        return session.read_to_prompt()
    if session.last_send_text.endswith("?"):
        text = session.read_to_prompt()
        session.sendline("")
        session.clean()
        return text

    return session.read_pod(_bgn_reo, _end_reo, _evt_reo)


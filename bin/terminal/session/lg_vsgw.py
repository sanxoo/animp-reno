import logging
import re

def open(session):
    seq = session.sys_info["seqs"]["1"]
    session.conn_seq = 1
    cmd = f"ssh {seq['id']}@{seq['ip']} -p {seq['port']}"
    logging.debug(f"1: {cmd}")
    session.spawn(cmd)
    index = session.expect(["password: ", "(yes/no/[fingerprint])? "])
    if index == 1:
        session.sendline("yes")
        session.expect("password: ")
    session.sendline(seq["pw"])
    session.expect(seq["prompt"])

    session.sendline("cd /home/ngepc/latest/bin")
    session.expect(seq["prompt"])

    seq = session.sys_info["seqs"]["2"]
    session.conn_seq = 2
    cmd = f"./esmmmc"
    logging.debug(f"2: {cmd}")
    session.sendline(cmd)
    session.expect("ID : ")
    session.sendline(seq["id"])
    session.expect("PASSWORD : ")
    session.sendline(seq["pw"])
    session.expect(seq["prompt"])

    session.passwd_pattern = "PASSWORD : "
    session.prompt_pattern = seq["prompt"]

def close(session):
    session.sendline("exit")
    session.sendline("exit")

def send(session, text):
    session.sendline(text)

_bgn_reo = re.compile("\d\d\d\d-\d\d-\d\d\s+\d\d:\d\d:\d\d")
_end_reo = re.compile("\s*COMPLETED")
_evt_reo = re.compile("[ \*]+[FAST]\d\d\d\d ")

def recv(session):
    if session.last_send_text.upper().startswith("HISTORY"):
        return session.read_to_prompt()
    if session.last_send_text.upper().startswith("SHOW"):
        return session.read_to_prompt()
    if session.last_send_text.upper().startswith("HELP"):
        return session.read_to_prompt()
    if session.last_send_text.endswith("?"):
        return session.read_to_prompt()

    return session.read_pod(_bgn_reo, _end_reo, _evt_reo)


import logging
import re

def open(session):
    seq = session.sys_info["seqs"]["2"]
    session.conn_seq = 1
    cmd = f"telnet {seq['ip']} {seq['port']}"
    logging.info(f"1: {cmd}")
    session.spawn(cmd)
    session.expect("Username : ")
    session.sendline("portbase")
    session.expect("Password : ")
    session.sendline("99999999")
    session.expect("***")

    session.sendline("")
    session.expect("LOGIN: ")
    session.sendline(seq["id"])
    session.expect("PASSWORD: ")
    session.sendline(seq["pw"])
    session.expect(seq["prompt"])
    session.sendline("")
    session.expect(seq["prompt"])

    session.sendline("INH-MSG:FLT;")
    session.expect(seq["prompt"])
    session.sendline("INH-MSG:STS;")
    session.expect(seq["prompt"])
    session.sendline("INH-MSG:ALM;")
    session.expect(seq["prompt"])

    session.passwd_pattern = "PASSWORD: "
    session.prompt_pattern = seq["prompt"]

def close(session):
    session.sendline("LOG-OUT;")

def send(session, text):
    session.sendline(text)

_bgn_reo = re.compile("\s+\S+\s+\d\d\d\d-\d\d-\d\d\s+\d\d:\d\d:\d\d\s+\S+\s+\S+\s+\S+\s+\S+")
_end_reo = re.compile("\s+COMPLETED|\s+CONTINUED")
_evt_reo = re.compile("[ \*]+[FAST]\d\d\d\d ")

def recv(session):
    if session.last_send_text.endswith("?"):
        return session.read_to_prompt()

    return session.read_pod(_bgn_reo, _end_reo, _evt_reo)


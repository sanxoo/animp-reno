import logging
import re

def open(session):
    seq = session.sys_info["seqs"]["1"]
    session.conn_seq = 1
    if seq["port"] == "22":
        cmd = f"ssh {seq['id']}@{seq['ip']} -p {seq['port']}"
        logging.debug(f"1: {cmd}")
        session.spawn(cmd)
        index = session.expect(["password: ", "(yes/no/[fingerprint])? "])
        if index == 1:
            session.sendline("yes")
            session.expect("password: ")
    else:
        cmd = f"telnet {seq['ip']} {seq['port']}"
        logging.debug(f"1: {cmd}")
        session.spawn(cmd)
        session.expect("login: ")
        session.sendline(seq["id"])
        session.expect("Password: ")
    session.sendline(seq["pw"])
    session.expect(seq["prompt"])

    seq = session.sys_info["seqs"]["2"]
    session.conn_seq = 2
    cmd = f"custerm"
    logging.debug(f"2: {cmd}")
    session.sendline(cmd)
    session.expect("Login: ")
    session.sendline(seq["id"])
    session.expect("Password: ")
    session.sendline(seq["pw"])
    index = session.expect("(yes/no): ")
    session.sendline("yes")
    session.expect(seq["prompt"])

    session.passwd_pattern = "Password: "
    session.prompt_pattern = seq["prompt"]

def close(session):
    session.sendline("exit")
    session.sendline("exit")

def send(session, text):
    session.sendline(text)

_bgn_reo = re.compile("\s*\S+\s+\d\d\d\d-\d\d-\d\d\s+\d\d:\d\d:\d\d\s+\S+\s+\S+\s+\S+")
_end_reo = re.compile("\s*COMPLETED|\s*CONTINUED")
_evt_reo = re.compile("[ \*]+[FAST]\d\d\d\d ")

def recv(session):
    if session.last_send_text.upper.startswith("DIS-ALM-INFO"):
        return session.read_to_prompt()
    if session.last_send_text.upper.startswith("DIS-ALM-STS"):
        return session.read_to_prompt()
    if session.last_send_text.upper.startswith("LIST"):
        return session.read_to_prompt()
    if session.last_send_text.upper.startswith("MAN"):
        return session.read_to_prompt()
    if session.last_send_text.upper.startswith("REFR"):
        return session.read_to_prompt()
    if session.last_send_text.upper.startswith("HELP"):
        return session.read_to_prompt()
    if session.last_send_text.startswith("?"):
        return session.read_to_prompt()
    if session.last_send_text.endswith("?"):
        return session.read_to_prompt()

    return session.read_pod(_bgn_reo, _end_reo, _evt_reo)


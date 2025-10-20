import logging
import re

def open(session):
    seq = session.sys_info["seqs"]["1"]
    session.conn_seq = 1
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

    session.sendline("stty columns 172 rows 45")
    session.expect(seq["prompt"])
    wd = "/PCRF/CLI_CLIENT/BIN" if "PCRF" in session.sys_info["name"] else "/PG/BIN/CLI"
    session.sendline(f"cd {wd}")
    session.expect(seq["prompt"])

    seq = session.sys_info["seqs"]["2"]
    session.conn_seq = 2
    cmd = f"CLI_CLIENT"
    logging.info(f"2: {cmd}")
    session.sendline(cmd)
    session.expect("Login : ")
    session.sendline(seq["id"])
    session.expect("Password : ")
    session.sendline(seq["pw"])
    session.expect(seq["prompt"])

    session.passwd_pattern = "password : "
    session.prompt_pattern = seq["prompt"]

def close(session):
    session.sendline("EXIT;")
    session.sendline("exit")

def send(session, text):
    session.sendline(text)

_bgn_reo = re.compile("\s+\S+\s+\d\d\d\d/\d\d/\d\d\s+\S+\s+\d\d:\d\d:\d\d")
_end_reo = re.compile(";")
_evt_reo = re.compile("[ \*]+[FAST]\d\d\d\d ")

def recv(session):
    if session.last_send_text.upper().startswith("FIND-CMD"):
        return wash(session.read_to_prompt())
    if session.last_send_text.upper().startswith("HELP"):
        return wash(session.read_to_prompt())
    if session.last_send_text.upper().startswith("?"):
        return wash(session.read_to_prompt())
    if session.last_send_text.upper().endswith("?"):
        return wash(session.read_to_prompt())

    return session.read_pod(_bgn_reo, _end_reo, _evt_reo)

def wash(text):
    podo = []
    for mess in text.splitlines():
        neat = ""
        for char in mess:
            neat = neat[:-1] if char == "" else neat + char
        podo.append(neat)
    return "\n".join(podo) + "\n\n"


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

    seq = session.sys_info["seqs"]["2"]
    session.conn_seq = 2
    snm = seq["prompt"][seq["prompt"].find(":")+1:seq["prompt"].find(")")]
    cmd = f"custerm"
    logging.debug(f"2: {cmd}")
    session.sendline(cmd)           # 0
    session.expect(") : ")
    session.sendline("")            # 1
    session.expect(") : ")
    session.sendline("")            # 2
    session.expect("  : ")
    session.sendline(seq["id"])     # 3
    session.expect("  : ")
    session.sendline(seq["pw"])     # 4
    session.expect(") : ")
    session.sendline("")            # 5
    session.expect(") : ")
    session.sendline("")            # 6
    session.expect(") : ")
    session.sendline("")            # 7
    session.expect(") : ")
    session.sendline(snm)           # 8
    session.expect(seq["prompt"])

    session.passwd_pattern = "Password: "
    session.prompt_pattern = seq["prompt"]

def close(session):
    session.sendline("quit")
    session.sendline("exit")

def send(session, text):
    session.sendline(text)

def recv(session):
    return session.read_to_prompt()


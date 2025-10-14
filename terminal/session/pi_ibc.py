import logging
import re

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
    session.expect("Enter)?")
    session.sendline()
    session.expect(seq["prompt"])

    session.passwd_pattern = "PWD:"
    session.prompt_pattern = seq["prompt"]

def close(session):
    session.sendline("exit")
    session.sendline("exit")

def send(session, text):
    session.sendline(text)

def recv(session):
    return session.read_to_prompt()


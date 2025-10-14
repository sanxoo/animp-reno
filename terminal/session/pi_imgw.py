import logging
import re

def open(session):
    seq = session.sys_info["seqs"]["1"]
    cmd = f"ssh {seq['id']}@{seq['ip']} -p {seq['port']}"
    logging.info(f"1: {cmd}")
    session.spawn(cmd)
    index = session.expect(["password: ", "(yes/no/[fingerprint])? "])
    if index == 1:
        session.sendline("yes")
        session.expect("password: ")
    session.sendline(seq["pw"])
    session.expect(seq["prompt"])

    seq = session.sys_info["seqs"]["2"]
    cmd = f"MMI"
    logging.info(f"2: {cmd}")
    session.sendline(cmd)
    session.expect("login: ")
    session.sendline(seq["id"])
    session.expect("Password: ")
    session.sendline(seq["pw"])
    session.expect("Enter)?")
    session.sendline("N")
    session.expect(f"CHG-SYS {session.sys_info['sys_name']}")
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


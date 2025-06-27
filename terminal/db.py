import logging

def get_system_info(system_id, service):
    return {
        "type": "wcdma_ss_msc", "id": "msc",
        "conn": [
            {"host": "192.168.101.224", "port": 22, "user": "sanxoo", "pswd": "tjddms00))", "prpt": "\x1b[0m$ "},
            {"host": "192.168.101.224", "port": 22, "user": "sanxoo", "pswd": "tjddms00))", "prpt": "\x1b[0m$ "},
        ],
        "port": 2000
    }

def hist_command(user, ip, text):
    ...

def hist_timeout(user, ip, text):
    ...


import logging

def get_reserved_info(date, time, weekday, dayofmonth, weekofmonth):
    ...

def get_system_info(system_id, service):
    return {
        "type": "wcdma_ss_msc", "id": "msc",
        "conn": [
            {"host": "192.168.101.224", "port": 22, "user": "sanxoo", "pswd": "tjddms00))", "prpt": "\x1b[0m$ "},
            {"host": "192.168.101.224", "port": 22, "user": "sanxoo", "pswd": "tjddms00))", "prpt": "\x1b[0m$ "},
        ],
        "port": 2000
    }

def get_reference():
    ...

def set_reference():
    ...

def get_rule():
    ...

def insert_check_list(reserved_info):
    ...

def get_check_list_item():
    ...

def set_check_list_item():
    ...


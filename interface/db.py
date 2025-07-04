
def get_system_info(system_id):
    return {}

def get_nms_info(nms_id, system_id=None):
    if system_id:
        return "password", 1, "01012341234", "t", 1
    return "password", 1

def get_nms_system_list(nms_no):
    return [
        ("NE001", 20001),
        ("NE002", 20002),
        ("NE003", 20003),
    ]

def log_nms_login(nms_no, desc):
    ...


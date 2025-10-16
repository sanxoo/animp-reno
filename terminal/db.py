import pymysql
import xml.etree.ElementTree

from common.config import settings
from common import cipher

def get_test_system_info():
    return {
        "sys_type": "test_dx_dev", "sys_name": "dxdev",
        "port": 20000,
        "seqs": {
            "1": {"ip": "192.168.101.224", "port": 22, "id": "sanxoo", "pw": "tjddms00))", "prompt": "$ "},
            "2": {"ip": "192.168.101.224", "port": 22, "id": "sanxoo", "pw": "tjddms00))", "prompt": "$ "},
        },
    }

def get_system_info(sys_name, svc_type):
    with pymysql.connect(**settings["maria"]) as conn:
        with conn.cursor() as curs:
            params = {
                "sys_name": sys_name,
            }
            select = (
                "SELECT SYSTEM_TYPE_NAME, PORT_MUX, PORT_SCH_MUX, SYSTEM_DATA "
                "FROM C_SYSTEM A, C_SYSTEM_TYPE B "
                "WHERE A.C_SYSTEM_TYPE_NO = B.C_SYSTEM_TYPE_NO AND SYSTEM_NAME = %(sys_name)s"
            )
            curs.execute(select, params)
            row = curs.fetchone()
            if not row: raise Exception(f"invalid system {sys_name}")
            sys_type, mux_port, sch_port, sys_data = row
    sys_info = {
        "sys_type": sys_type, "sys_name": sys_name,
        "port": mux_port if svc_type != "daycheck" else sch_port,
        "seqs": {},
    }
    for eip in xml.etree.ElementTree.fromstring(sys_data).iterfind("EIP"):
        seq = {e.tag.lower():e.text for e in eip}
        seq.update({"pw": cipher.decrypt(seq["pw"])})
        sys_info["seqs"][seq.pop("seq")] = seq
    return sys_info


if __name__ == "__main__":
    import json
    sys_info = get_system_info("MSC201", "terminal")
    print(json.dumps(sys_info, indent=4))


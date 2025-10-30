import pymysql
import xml.etree.ElementTree

from lib.common import config
from lib import cipher

def get_system_info(sys_name, svc_type):
    if sys_name.lower() == "test":
        return {
            "sys_type": "test_uv_xyz", "sys_name": sys_name, "port": 20000,
            "seqs": {
                "1": {"ip": "192.168.101.224", "port": 22, "id": "sanxoo", "pw": "tjddms00))", "prompt": "$ "},
                "2": {"ip": "192.168.101.224", "port": 22, "id": "sanxoo", "pw": "tjddms00))", "prompt": "$ "},
            },
        }
    with pymysql.connect(**config["maria"]) as conn:
        with conn.cursor() as curs:
            params = {
                "sys_name": sys_name,
            }
            select = (
                "SELECT SYSTEM_TYPE_NAME, PORT_MUX, PORT_SCH_MUX, SYSTEM_DATA "
                "FROM C_SYSTEM A, C_SYSTEM_TYPE B "
                "WHERE A.C_SYSTEM_TYPE_NO = B.C_SYSTEM_TYPE_NO AND SYSTEM_NAME = %(sys_name)s "
            )
            curs.execute(select, params)
            row = curs.fetchone()
            if not row: raise Exception(f"invalid system {sys_name}")
    sys_type, mux_port, sch_port, sys_data = row
    sys_info = {
        "sys_type": sys_type, "sys_name": sys_name, "port": sch_port if svc_type == "daycheck" else mux_port,
        "seqs": {},
    }
    for eip in xml.etree.ElementTree.fromstring(sys_data).iterfind("EIP"):
        seq = {e.tag.lower():e.text for e in eip}
        seq.update({
            "id": seq["id"] and cipher.decrypt(seq["id"]), "pw": seq["pw"] and cipher.decrypt(seq["pw"]),
            "ip": seq["ip"] and cipher.decrypt(seq["ip"]),
        })
        sys_info["seqs"][seq.pop("seq")] = seq
    return sys_info


if __name__ == "__main__":
    import json
    sys_info = get_system_info("MSC201", "terminal")
    print(json.dumps(sys_info, indent=4))


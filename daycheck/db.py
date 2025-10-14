import pymysql
import xml.etree.ElementTree

import API.M6 as M6

from common.config import settings
from common import cipher

def get_reserved_list(params):
    with pymysql.connect(**settings["maria"]) as conn:
        with conn.cursor() as curs:
            select = (
                "SELECT A.C_SYSTEM_NO, SYSTEM_NAME, AUTOCHK_ID, ORD_SEQ, COD_NAME, CYCLE_TYPE, VIEW_TYPE, NOK_TYPE, CHECK_ID, USER_ID "
                "FROM C_AUTOCHK_RESERVE A, C_SYSTEM B "
                "WHERE A.C_SYSTEM_NO = B.C_SYSTEM_NO AND VALID_DATE IN (%(date)s, NULL, '') AND CYCLE_TIME = %(time)s "
                "AND DEL_FLAG = 'USE' AND START_FLAG = 'Y' AND USE_YN = 'Y' AND A.C_TEAM_ID IN %(team_id)s "
                "AND ( CYCLE_TYPE = 'D' "
                " OR ( CYCLE_TYPE = 'W' AND CYCLE_DAY = %(isoweekday)s ) "
                " OR ( CYCLE_TYPE = 'M' AND CYCLE_DAY = %(day_of_month)s ) "
                " OR ( CYCLE_TYPE = 'M' AND SUBSTR(CYCLE_DAY, 1, 1) = %(week_of_month)s AND SUBSTR(CYCLE_DAY, 3, 1) = %(isoweekday)s ) "
                ") "
            )
            curs.execute(select, params)
            return curs.fetchall()

def insert_check_list(reserved_list, times):
    try:
        iris = settings["iris"]
        conn = M6.Connection(iris["master"], iris["user"], iris["password"], Database=iris["database"])
        curs = conn.Cursor()
        insert = (
            "INSERT INTO D_CHKLIST_RESULT ( C_SYSTEM_NO, SYSTEM_NAME, AUTO_START_FLAG, AUTOCHK_ID, ORD_SEQ, COD_NAME, COD_STATE, COD_TIME, "
            "CYCLE_TYPE, VIEW_TYPE, NOK_TYPE, CHECK_ID, USER_ID, REAL_TIME, EVT_TIME ) "
        )
        for sys_no, sys_name, autochk_id, seq, cod, cycle_type, view_type, nok_type, chk_id, user_id in reserved_list:
            cod = cod.replace("'", "''")
            values = (
                f"VALUES ( '{sys_no}', '{sys_name}', 'Y', '{autochk_id}', '{seq}', '{cod}', '0', '{times['min']}', "
                f"'{cycle_type}', '{view_type}', '{nok_type}', '{chk_id}', '{user_id}', '{times['min']}', '{times['evt']}' );"
            )
            res = curs.Execute2(insert + values)
            if not res.startswith("+OK"): raise Exception(res)
    finally:
        curs.Close()
        conn.close()

def get_system_info(sys_name):
    with pymysql.connect(**settings["maria"]) as conn:
        with conn.cursor() as curs:
            params = {
                "sys_name": sys_name,
            }
            select = (
                "SELECT C_SYSTEM_NO, PORT_MUX, PORT_SCH_MUX, PORT_EVENT_LOCAL, SYSTEM_DATA, SYSTEM_TYPE_NAME, A.CLI_PREFIX, SYSEVT_LOCAL_PORT "
                "FROM C_SYSTEM A, C_SYSTEM_TYPE B, C_TEAM C "
                "WHERE A.C_SYSTEM_TYPE_NO = B.C_SYSTEM_TYPE_NO AND B.C_TEAM_ID = C.C_TEAM_ID "
                "AND SYSTEM_NAME = %(sys_name)s"
            )
            curs.execute(select, params)
            row = curs.fetchone()
            if not row: raise Exception(f"invalid system {sys_name}")
            sys_no, mux_port, sch_port, evt_port, sys_data, sys_type, prefix, sysevt_port = row
    sys_info = {
        "sys_name": sys_name, "sys_no": sys_no, "mux_port": mux_port, "sch_port": sch_port, "evt_port": evt_port,
        "sys_type": sys_type, "prefix": prefix, "sysevt_port": sysevt_port,
        "seq": {},
    }
    for eip in xml.etree.ElementTree.fromstring(sys_data).iterfind("EIP"):
        seq = {e.tag.lower():e.text for e in eip}
        seq.update({"pw": cipher.decrypt(seq["pw"])})
        sys_info["seq"] = seq
    return sys_info

def get_check_item_count(sys_no, partition_from):
    try:
        iris = settings["iris"]
        conn = M6.Connection(iris["master"], iris["user"], iris["password"], Database=iris["database"])
        curs = conn.Cursor()
        curs.SetRecordSep("|&|")
        curs.SetFieldSep("|^|")
        select = (
            f"/*+ LOCATION ( KEY = {sys_no} AND {partition_from} <= PARTITION ) */ "
            f"SELECT COUNT(*) "
            f"FROM D_CHKLIST_RESULT "
            f"WHERE COD_STATE = '0';"
        )
        res = curs.Execute2(select)
        if not res.startswith("+OK"): raise Exception(res)
        row = curs.Fetchone()
        if not row: return 0
        return row[0]
    finally:
        curs.Close()
        conn.close()

def get_check_item(sys_no, partition_from):
    try:
        iris = settings["iris"]
        conn = M6.Connection(iris["master"], iris["user"], iris["password"], Database=iris["database"])
        curs = conn.Cursor()
        curs.SetRecordSep("|&|")
        curs.SetFieldSep("|^|")
        select = (
            f"/*+ LOCATION ( KEY = {sys_no} AND {partition_from} <= PARTITION ) */ "
            f"SELECT C_SYSTEM_NO, EVT_TIME, AUTOCHK_ID, COD_NAME, COD_STATE, COD_TIME, RERUN_NUM, CYCLE_TYPE, VIEW_TYPE, NOK_TYPE, CHECK_ID "
            f"FROM D_CHKLIST_RESULT "
            f"WHERE COD_STATE = '0' "
            f"ORDER BY EVT_TIME, AUTOCHK_ID, ORD_SEQ LIMIT 1;"
        )
        res = curs.Execute2(select)
        if not res.startswith("+OK"): raise Exception(res)
        row = curs.Fetchone()
        if not row: return {}
        key = [ "sys_no", "evt_time", "autochk_id", "cod", "cod_state", "cod_time", "rerun_num", "cycle_type", "view_type", "nok_type", "chk_id" ]
        return dict(zip(key, row))
    finally:
        curs.Close()
        conn.close()

def update_check_item(item):
    try:
        iris = settings["iris"]
        conn = M6.Connection(iris["master"], iris["user"], iris["password"], Database=iris["database"])
        curs = conn.Cursor()
        partition = item["evt_time"][:8] + "000000"
        reason = item["reason"].repalce("'", "''")
        raw_pod = item["raw_pod"].repalce("'", "''")
        cmp_pod = item["cmp_pod"].repalce("'", "''")
        std_pod = item["std_pod"].repalce("'", "''")
        cod = item["cod"].repalce("'", "''")
        update = (
            f"/*+ LOCATION ( KEY = {item['sys_no']} AND PARTITION = {partition} ) */ "
            f"UPDATE D_CHKLIST_RESULT SET "
            f"COD_STATE = '{item['cod_state']}', STANDARD_DATE = '{item['std_date']}', "
            f"POD_TIME = '{item['pod_time']}', POD_RESULT = '{item['pod_result']}', REASON = '{reason}', "
            f"POD_RAW = '{raw_pod}', POD_COMPARE = '{cmp_pod}', POD_STANDARD = '{std_pod}' "
            f"WEHRE AUTOCHK_ID = '{item['autochk_id']}' "
            f"AND COD_NAME = '{cod}' AND COD_TIME = '{item['cod_time']}' AND RERUN_NUM = '{item['rerun_num']}';"
        )
        res = curs.Execute2(update)
        if not res.startswith("+OK"): raise Exception(res)
    finally:
        curs.Close()
        conn.close()

def get_standard_pod(item):
    with pymysql.connect(**settings["maria"]) as conn:
        with conn.cursor() as curs:
            params = {
                "sys_no": item["sys_no"], "cod": item["cod"].repalce("'", "''"),
            }
            select = (
                "SELECT C_SYSTEM_NO, COD_NAME, CYCLE_TYPE, RESULT_TYPE, POD_STANDARD, STANDARD_DATE, USER_ID, C_TEAM_ID "
                "FROM C_CHKLIST_STANDARD "
                "WHERE C_SYSTEM_NO = %(sys_no)s AND COD_NAME = %(cod)s "
            )
            curs.execute(select, params)
            row = curs.fetchone()
            if not row: return {}
            key = [ "sys_no", "cod", "cycle_type", "res_type", "std_pod", "std_date", "user_id", "team_id" ]
            return dict(zip(key, row))

def insert_standard_pod(std_pod):
    with pymysql.connect(**settings["maria"]) as conn:
        with conn.cursor() as curs:
            params = {
                **std_pod, "cod": std_pod["cod"].repalce("'", "''"), "std_pod": std_pod["std_pod"].repalce("'", "''"),
            }
            insert = (
                "INSERT INTO C_CHKLIST_STANDARD ( C_SYSTEM_NO, COD_NAME, CYCLE_TYPE, RESULT_TYPE, POD_STANDARD, STANDARD_DATE, USER_ID, C_TEAM_ID ) "
                "VALUES ( %(sys_no)s, %(cod)s, %(cycle_type)s, %(res_type)s, %(std_pod)s, %(std_date)s, %(user_id)s, %(team_id)s ) "
            )
            curs.execute(insert, params)
            conn.commit()


if __name__ == "__main__":
    import json
    reserved_info = get_reserved_info({
        "date": "20250924",
        "time": "0630",
        "isoweekday": 6,
        "day_of_month": 24,
        "week_of_month": 4,
        "team_id": ["00001200", "00001621"],
    })
    print(json.dumps(reserved_info, indent=4))


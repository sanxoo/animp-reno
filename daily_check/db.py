import logging
import pymysql

from common.config import settings
from common import cipher

def gen_check_items(params):
    with pymysql.connect(**settings["maria"]) as conn:
        with conn.cursor() as curs:
            select = (
                "SELECT A.C_SYSTEM_NO, SYSTEM_NAME, AUTOCHK_ID, ORD_SEQ, COD_NAME, CYCLE_TYPE, VIEW_TYPE, NOK_TYPE, CHECK_ID, USER_ID, TEAM_ID "
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
            row = curs.fetchall()
            logging.info(f"gen {len(row)} check items")
    if not row: return
    try:
        iris = settings["iris"]
        conn = M6.Connection(iris["master"], iris["user"], iris["password"], Database=iris["database"])
        curs = conn.Cursor()
        insert = (
            "INSERT INTO D_CHKLIST_RESULT ( C_SYSTEM_NO, SYSTEM_NAME, AUTO_START_FLAG, AUTOCHK_ID, ORD_SEQ, COD_NAME, COD_STATE, COD_TIME, "
            "CYCLE_TYPE, VIEW_TYPE, NOK_TYPE, CHECK_ID, USER_ID, TEAM_ID, REAL_TIME, EVT_TIME ) "
        )
        for sys_no, sys_name, autochk_id, seq, cod, cycle_type, view_type, nok_type, chk_id, user_id, team_id in row:
            cod = cod.replace("'", "''")
            values = (
                f"VALUES ( '{sys_no}', '{sys_name}', 'Y', '{autochk_id}', '{seq}', '{cod}', '0', '{params['minute']}', "
                f"'{cycle_type}', '{view_type}', '{nok_type}', '{chk_id}', '{user_id}', '{team_id}', '{params['minute']}', '{params['evt_time']}' );"
            )
            res = curs.Execute2(insert + values)
            if not res.startswith("+OK"): raise Exception(res)
    finally:
        curs.Close()
        conn.close()

def get_system_info(sys_name):
    with pymysql.connect(**settings["maria"]) as conn:
        with conn.cursor() as curs:
            select = (
                "SELECT C_SYSTEM_NO, PORT_MUX, PORT_SCH_MUX, PORT_EVENT_LOCAL, SYSTEM_DATA, SYSTEM_TYPE_NAME, A.CLI_PREFIX, SYSEVT_LOCAL_PORT "
                "FROM C_SYSTEM A, C_SYSTEM_TYPE B, C_TEAM C "
                "WHERE A.C_SYSTEM_TYPE_NO = B.C_SYSTEM_TYPE_NO AND B.C_TEAM_ID = C.C_TEAM_ID "
                "AND SYSTEM_NAME = %(sys_name)s"
            )
            curs.execute(select, {"sys_name": sys_name,})
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
            f"SELECT C_SYSTEM_NO, EVT_TIME, AUTOCHK_ID, COD_NAME, COD_STATE, COD_TIME, RERUN_NUM, CYCLE_TYPE, VIEW_TYPE, NOK_TYPE, CHECK_ID, TEAM_ID "
            f"FROM D_CHKLIST_RESULT "
            f"WHERE COD_STATE = '0' "
            f"ORDER BY EVT_TIME, AUTOCHK_ID, ORD_SEQ LIMIT 1;"
        )
        res = curs.Execute2(select)
        if not res.startswith("+OK"): raise Exception(res)
        row = curs.Fetchone()
        if not row: return {}
        key = ["sys_no", "evt_time", "autochk_id", "cod", "cod_state", "cod_time", "rerun_num", "cycle_type", "view_type", "nok_type", "chk_id", "team_id"]
        return dict(zip(key, row))
    finally:
        curs.Close()
        conn.close()

def put_check_item(chk_item):
    try:
        iris = settings["iris"]
        conn = M6.Connection(iris["master"], iris["user"], iris["password"], Database=iris["database"])
        curs = conn.Cursor()
        partition = chk_item["evt_time"][:8] + "000000"
        reason = chk_item["reason"].repalce("'", "''")
        fmt_pod = chk_item["fmt_pod"].repalce("'", "''")
        cmp_pod = chk_item["cmp_pod"].repalce("'", "''")
        std_pod = chk_item["std_pod"].repalce("'", "''")
        cod = chk_item["cod"].repalce("'", "''")
        update = (
            f"/*+ LOCATION ( KEY = {item['sys_no']} AND PARTITION = {partition} ) */ "
            f"UPDATE D_CHKLIST_RESULT SET "
            f"COD_STATE = '{chk_item['cod_state']}', STANDARD_DATE = '{chk_item['std_date']}', "
            f"POD_TIME = '{chk_item['pod_time']}', POD_RESULT = '{chk_item['pod_result']}', REASON = '{reason}', "
            f"POD_RAW = '{fmt_pod}', POD_COMPARE = '{cmp_pod}', POD_STANDARD = '{std_pod}' "
            f"WEHRE AUTOCHK_ID = '{chk_item['autochk_id']}' "
            f"AND COD_NAME = '{cod}' AND COD_TIME = '{chk_item['cod_time']}' AND RERUN_NUM = '{chk_item['rerun_num']}';"
        )
        res = curs.Execute2(update)
        if not res.startswith("+OK"): raise Exception(res)
    finally:
        curs.Close()
        conn.close()

def get_standard_pod(chk_item):
    with pymysql.connect(**settings["maria"]) as conn:
        with conn.cursor() as curs:
            select = (
                "SELECT POD_STANDARD, STANDARD_DATE "
                "FROM C_CHKLIST_STANDARD "
                "WHERE C_SYSTEM_NO = %(sys_no)s AND COD_NAME = %(cmd)s "
            )
            curs.execute(select, chk_item)
            row = curs.fetchone()
            if not row: return {}
            key = ["std_pod", "std_date"]
            return dict(zip(key, row))

def put_standard_pod(chk_item):
    with pymysql.connect(**settings["maria"]) as conn:
        with conn.cursor() as curs:
            params = {
                **chk_item, "std_pod": std_pod["std_pod"].repalce("'", "''"),
            }
            insert = (
                "INSERT INTO C_CHKLIST_STANDARD ( C_SYSTEM_NO, COD_NAME, CYCLE_TYPE, RESULT_TYPE, POD_STANDARD, STANDARD_DATE, USER_ID, C_TEAM_ID ) "
                "VALUES ( %(sys_no)s, %(cmd)s, %(cycle_type)s, 'A', %(std_pod)s, %(std_date)s, 'ANIMP', %(team_id)s ) "
            )
            curs.execute(insert, params)
            conn.commit()

def get_eval_rule(chk_item):
    with pymysql.connect(**settings["maria"]) as conn:
        with conn.cursor() as curs:
            select = (
                "SELECT BEGIN_PTN, END_PTN, DATA_LINE, SKIP_PTN, TARGET_LINE, VALID_LINE, COMPARE_RESULT "
                "FROM C_GENPARSER_CONF "
                "WHERE SECTION = %(cmd)s AND TEAM_ID = %(team_id)s "
            )
            curs.execute(select, chk_item)
            return curs.fetchone()



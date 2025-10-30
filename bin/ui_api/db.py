import pymysql

from lib.common import config

def get_api_port():
    with pymysql.connect(**config["maria"]) as conn:
        with conn.cursor() as curs:
            params = {
                "team_id": config["team_id"],
            }
            select = (
                "SELECT CAST(CMDS_PORT AS UNSIGNED) FROM C_TEAM WHERE C_TEAM_ID IN %(team_id)s "
            )
            curs.execute(select, params)
            row = curs.fetchone()
            if not row: raise Exception(f"invalid system {sys_name}")
    api_port, = row
    return api_port


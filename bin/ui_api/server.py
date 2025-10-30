import logging
import traceback

from functools import wraps

from fastapi import FastAPI, Depends, Header, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from lib.common import config, set_logger
from lib import cipher
from bin.terminal import db, session

def valid_auth_key(auth_key: str = Header(...)):
    if auth_key == config["ui_api"]["auth_key"]:
        return
    raise HTTPException(401, detail=[{"type": "internal_error", "msg": "unauthorized"}])

def murmur(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logging.info(f"{args} {kwargs}")
            return func(*args, **kwargs)
        except HTTPException:
            raise
        except:
            logging.exception("")
            raise HTTPException(500, detail=[{"type": "internal_error", "msg": traceback.format_exc()}])
    return wrapper

app = FastAPI() #dependencies=[Depends(valid_auth_key)])

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

@app.post("/api/test/connecting", status_code=200)
@murmur
def test_connecting(body: dict = Body(...)):
    sys_name = body["systemName"]
    sys_info = db.get_system_info(sys_name, "terminal")
    res = {
        "systemName": sys_name, "list": [],
    }
    for seq in body["list"]:
        sys_info["seqs"][seq["seq"]].update({
            "id": seq["id"] and cipher.decrypt(seq["id"]), "pw": seq["pw"] and cipher.decrypt(seq["pw"]),
            "ip": seq["ip"] and cipher.decrypt(seq["ip"]),
        })
        res["list"].append({**seq, "resultCode": 0, "resultMessage": ""})
    try:
        session.open(sys_info, test=True).close()
    except Exception as e:
        seq, msg = str(e).split(",", 1)
        res["list"][int(seq)-1].update({"resultCode": 1, "resultMessage": msg})
    return res

if __name__ == "__main__":
    from bin.ui_api.db import get_api_port
    import uvicorn
    set_logger(f"ui_api.log")
    uvicorn.run(app, host="0.0.0.0", port=get_api_port())


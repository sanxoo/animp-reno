import logging
import traceback

from functools import wraps

from fastapi import FastAPI, Depends, Header, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from common.config import settings

def valid_auth_key(auth_key: str = Header(...)):
    if auth_key == settings["auth_key"]:
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
def test_conn(body: dict = Body(...)):
    return body


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)


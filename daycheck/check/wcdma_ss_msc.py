import logging
import re

from check import format, color

def rtrv_date(pod):
    ptn = r"(\d{4}-\d\d-\d\d\s+\d\d:\d\d:\d\d)"
    ref = ""
    nok = 0
    txt = ""
    for i in pod.splitlines():
        cno = color.black
        mch = re.search(ptn, i)
        if mch:
            if not ref: ref = mch.group(1)
            cno = color.blue
            if ref and ref != mch.group(1):
                nok = nok + 1
                cno = color.red
        txt += format(i, cno)
    return nok == 0, txt


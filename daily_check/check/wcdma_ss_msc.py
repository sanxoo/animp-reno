import logging
import re

from daily_check import check

def rtrv_date(pod):
    ptn = r"(\d{4}-\d\d-\d\d\s+\d\d:\d\d:\d\d)"
    ref = ""
    nok = 0
    txt = ""
    for i in pod.splitlines():
        cno = check.Color.BLACK
        mch = re.search(ptn, i)
        if mch:
            if not ref: ref = mch.group(1)
            cno = check.Color.BLUE
            if ref and ref != mch.group(1):
                nok = nok + 1
                cno = check.Color.RED
        txt += check.format(i, cno)
    return txt, nok == 0


import enum
import difflib
import re

class Color(enum.IntEnum):
    BLACK = 0
    BLUE = 1
    RED = 2
    GREY = 3

def format(i, cno):
    return f"\\cf{cno} {i} \\par\n"

def compare(pod, reference):
    res = difflib.ndiff(reference.splitlines(), pod.splitlines())
    ptn = r"\d{4}-\d\d-\d\d"
    nok, mns, pls = 0, 0, 0
    txt = ""
    for i in res:
        if i.startswith("? "): continue
        cno = Color.BLACK
        if i.startswith("- "):
            if not re.search(ptn, i): nok += 1
            mns, cno = mns + 1, Color.RED
        if i.startswith("+ "):
            if not re.search(ptn, i): nok += 1
            pls, cno = pls + 1, Color.BLUE
        txt += format(i, cno)
    return txt, nok == 0 and mns == pls

def evaluate(pod, rule):
    bgn, end, skp, ign, tgt, cnd, dcs = rule
    stt, cnt, aok = 0, 0, True
    txt = ""
    for i in pod.splitlines():
        if stt == 0:
            if not bgn or re.search(bgn, i):
                stt, cnt = 1, skp
        if stt == 1:
            stt = 2 if cnt < 1 else stt
            cnt = cnt - 1
        if stt != 0:
            if i and end and re.search(end, i): stt = 0
        cno = Color.BLACK
        if stt == 2:
            if i and ign and re.search(ign, i): cno = Color.GREY
            else:
                if i and not tgt or re.search(tgt, i):
                    knd, exp = cnd.split(",", 1)
                    tkn = i.split()
                    res = eval(replace(exp, tkn)) if knd == "#PY#" else eval_equals(exp, tkn, knd == "#OR#")
                    aok = aok and res
                    cno = Color.BLUE if res else Color.RED
        txt += format(i, cno)
    return txt, not aok if dcs.lower() == "nok" else aok

def replace(exp, tkn):
    for i in range(len(tkn) - 1, -1, -1): exp = exp.replace(f"${i}", tkn[i])
    return exp

def eval_equals(exp, tkn, _or):
    res = not _or
    for eqn in exp.split(","):
        lft, rgt = [i.strip() for i in replace(eqn, tkn).split("=")]
        res = res or lft == rgt if _or else res and lft == rgt
    return res

def func(system_type, cod):
    try:
        module = importlib.import_module(f"bin.daily_check.checker.{system_type.lower()}")
        name = cod.lower().replace("-", "_")
        return getattr(module, name)
    except:
        logging.exception("")
    return None



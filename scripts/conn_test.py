import logging

from terminal import db, session

def main():
    sys_info = db.get_test_system_info()
    try:
        sess = session.open(sys_info, test=True)
        sess.close()
        print(f"SUCC")
    except Exception as e:
        print(f"FAIL|{str(e)}")

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelno)s %(filename)s:%(lineno)03d - %(message)s",
        level=logging.INFO, #DEBUG,
    )
    main()


import logging
import sys

import server
import db

def main():
    try:
        system_id, service = sys.argv[1:]
        system_info = db.get_system_info(system_id, service)
        serv = server.server(system_info)
        serv.run()
    except:
        logging.exception("")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stderr.write(f"\nusage: {sys.argv[0]} system_id terminal|daycheck\n\n")
        sys.exit()
    logging.basicConfig(level=logging.DEBUG)
    main()


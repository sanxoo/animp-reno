import logging
import sys

import consumer

def main():
    try:
        system_id = sys.argv[1]
        serv = consumer.consumer(system_id)
        serv.run()
    except:
        logging.exception("")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write(f"\nusage: {sys.argv[0]} system_id\n\n")
        sys.exit()
    logging.basicConfig(level=logging.DEBUG)
    main()


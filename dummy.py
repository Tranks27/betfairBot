import time
# import constants
# arr = ['12.0','125.0','12.0','32.0','959','2.0' ]

# cnt = 0
# while cnt < constants.NUM_GAMES:
#     cnt = cnt + 1
#     print(cnt)
#     time.sleep(1)
#########################################################################
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
liability_options = [50, 50, 50, 50, 50, 1500, 50, 50, 50, 1500] #not sure why this can't be moved into constants.py
logging.info("liability_options [BEFORE] = %s , LENGTH = %d", liability_options, len(liability_options))
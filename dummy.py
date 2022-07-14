import time
# import constants
# arr = ['12.0','125.0','12.0','32.0','959','2.0' ]

# cnt = 0
# while cnt < constants.NUM_GAMES:
#     cnt = cnt + 1
#     print(cnt)
#     time.sleep(1)
#########################################################################
# import logging

# def failGracefully(error='N/A'):
#     logging.error("Error: {0}".format(error) )
#     # logging.error("Error: %s", (error) )
#     logging.info("Moving to next match")
#     logging.error("********************************************************\n\n\n")

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     handlers=[
#         logging.FileHandler("temp.log"),
#         logging.StreamHandler()
#     ]
# )

# try:
#     x = 10/0
# except Exception as e:
#     logging.info("Fatal error in main loop")
#     failGracefully(e)

#########################################################################
import datetime
import pytz
startTime = 0
print(startTime)
timeNow = (datetime.datetime.now(pytz.timezone("Europe/London"))-datetime.timedelta(hours=1)) ## minus 1 hr due to daylight savings maybe?
startTime = timeNow.replace(tzinfo=pytz.UTC)
    
    
print("Market Start Time: %s", startTime)
# import time
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
# import datetime
# import pytz
# startTime = 0
# print(startTime)
# timeNow = (datetime.datetime.now(pytz.timezone("Europe/London"))-datetime.timedelta(hours=1)) ## minus 1 hr due to daylight savings maybe?
# startTime = timeNow.replace(tzinfo=pytz.UTC)
    
    
# print("Market Start Time: %s", startTime)
#########################################################################
# odds = ['99', '99', '99', '99', '99', '99']

# if '-1' in odds:
#     print("True")


#########################################################################
pos1 = 0
pos2 = 0
odds_arr = ['8.70', '4.70', '9.50', '3.00', '3.70', '9.00']
if '99' in odds_arr:
    scratched_index = odds_arr.index('99')
    print("scratched index = " , scratched_index)
# sorted_odds = ['3.70', '3.70', '4.60', '5.00', '5.50', '9.00']
sorted_odds = sorted(odds_arr,key=float)
print("sorted odds = ", sorted_odds)
pos1 = odds_arr.index(sorted_odds[0]) 
# odds_arr.remove(sorted_odds[0])
# print(odds_arr)
## Check if there are duplicates and act accordingly
if sorted_odds[0] == sorted_odds[1]:
    pos2 = odds_arr.index(sorted_odds[1], pos1+1) # search after the first duplicate
else:
    pos2 = odds_arr.index(sorted_odds[1])


print("Forecast = ", pos1+1, pos2+1)

#########################################################################
## Choose the index of the lay selection out of 30 options or less
coordinates = []

for x in range(6):
    for y in range(6):
        if(x != y):
            if('99' in odds_arr):
                if(x != scratched_index and y != scratched_index):
                    coordinates.append((x, y))
            else:
                coordinates.append((x, y))

print(coordinates, "length = ", len(coordinates))

# res = [x+1 for x,y in enumerate(coordinates) if (y[0] ==pos1 and y[1] == pos2) ]
res = [x for x,y in enumerate(coordinates) if (y[0] ==pos1 and y[1] == pos2) ]
print("lay_id index = ", res[0])
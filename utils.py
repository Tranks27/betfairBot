from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import pandas as pd

import time
import datetime
import pytz
import csv
import numpy as np
from app import logging
#########################################################
## External functions
#########################################################

###
# function from betfair tutorial
###
def process_runner_books(runner_books):
    '''
    This function processes the runner books and returns a DataFrame with the best back/lay prices + vol for each runner
    :param runner_books:
    :return:
    '''
    # best_back_prices = [runner_book.ex.available_to_back[0].price
    #                     if runner_book.ex.available_to_back
    #                     else 1.01
    #                     for runner_book
    #                     in runner_books]
    # best_back_sizes = [runner_book.ex.available_to_back[0].size
    #                    if runner_book.ex.available_to_back
    #                    else 1.01
    #                    for runner_book
    #                    in runner_books]

    best_lay_prices = [runner_book.ex.available_to_lay[0].price
                       if runner_book.ex.available_to_lay
                       else 1000.0
                       for runner_book
                       in runner_books]
    best_lay_sizes = [runner_book.ex.available_to_lay[0].size
                      if runner_book.ex.available_to_lay
                      else 1.01
                      for runner_book
                      in runner_books]
    
    ## CHECK if the market is mature based on Back Market Percentage (aka over-rounds)
    print(best_lay_prices)
    inverse = [1/float(x) for x in best_lay_prices]
    bmp_percent = int(sum(inverse) * 100)
    print("BMP_percent = ", bmp_percent)
    if bmp_percent < 85 or bmp_percent > 100: ## values recommended by betfair bot manager
        print("Market not mature. SKIP")
        return -1

    ## Continue
    selection_ids = [runner_book.selection_id for runner_book in runner_books]
    last_prices_traded = [runner_book.last_price_traded for runner_book in runner_books]
    total_matched = [runner_book.total_matched for runner_book in runner_books]
    statuses = [runner_book.status for runner_book in runner_books]
    # scratching_datetimes = [runner_book.removal_date for runner_book in runner_books]
    # adjustment_factors = [runner_book.adjustment_factor for runner_book in runner_books]

    df = pd.DataFrame({
        'Selection ID': selection_ids,
        # 'Best Back Price': best_back_prices,
        # 'Best Back Size': best_back_sizes,
        'Best Lay Price': best_lay_prices,
        'Best Lay Size': best_lay_sizes,
        'Last Price Traded': last_prices_traded,
        'Total Matched': total_matched,
        'Status': statuses,
        # 'Removal Date': scratching_datetimes,
        # 'Adjustment Factor': adjustment_factors
    })
    return df

###
# Returns the exacta from NEDS
###
def choose_lay_option_neds(venueName):
    odds_arr = get_odds(venueName) # try getting the odds
    if '-1' in odds_arr: # try a second time if result is empty
        odds_arr = get_odds(venueName)
    logging.info("odds_arr = %s", odds_arr)

    ## Check if the odds_arr is empty
    if '-1' in odds_arr:
        logging.error("Neds api 2nd attempt failed")
        logging.info("odds_arr = %s", odds_arr)
        return -3
    
    ## Check if no price is advertised
    if 'SP' in odds_arr:
        logging.info('Only SP data provided by NEDs, SKIP')
        logging.info("odds_arr = %s", odds_arr)
        return -4

    ## Check if the odds are a float number as it should be
    if isFloat(odds_arr[0]) == False:
        logging.info('The odds are not float numbers, SKIP')
        logging.info("odds_arr = %s", odds_arr)
        return -5

    ## Avoid if there are less than 5 runners
    if '99' in odds_arr: ## If there's a scratched runner
        num_scratched = np.where(np.array(odds_arr) == '99')[0]
        ## if there are more than one scratched runners, skip
        if len(num_scratched) > 1:
            logging.error("More than 1 runner scratched")
            return -2
        else:
            scratched_index = odds_arr.index('99')
            logging.info("scratched index = %d", scratched_index+1)
            logging.info("Only 1 runner scratched, proceed")
        # return -2

    ## Check the lowest odds and highest odds follow my criteria
    tooLowCnt = 0
    tooHighCnt = 0
    for i in odds_arr:
        if(float(i) < 2.6):
            tooLowCnt = tooLowCnt + 1
        if(float(i) > 9.9):
            tooHighCnt = tooHighCnt + 1
    if tooLowCnt > 1 or tooHighCnt > 1:
        logging.info("The odds are extreme. SKIP")
        logging.info("odds_arr = %s", odds_arr)
        return -6
        
    ## Sort out the odds_arr
    sorted_odds = sorted(odds_arr,key=float)
    logging.info("sorted_odds = %s", sorted_odds)
    
    pos1 = 0
    pos2 = 0
    pos1 = odds_arr.index(sorted_odds[0]) 
    ## Deal with min odds duplicates
    if sorted_odds[0] == sorted_odds[1]:
        pos2 = odds_arr.index(sorted_odds[1], pos1+1) # search after the first duplicate
    else:
        pos2 = odds_arr.index(sorted_odds[1])
    # pos3 = odds_arr.index(sorted_odds[2]) 
    logging.info("Forecast = %d - %d", pos1+1, pos2+1)

    ## TODO: avoid if the 3 lowest odds are similar ## EDIT: We want to include the races with same lowest odds as well
    # if pos1 == pos2 or pos2 == pos3:
    #     logging.error("2 same odds found")
    #     logging.info('Two of the 3 smallest odds are the same : pos1 = %d, pos2 = %d, pos3 = %d', pos1, pos2, pos3)
    #     return -1

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

    # res = [x+1 for x,y in enumerate(coordinates) if (y[0] ==pos1 and y[1] == pos2) ]
    res = [x for x,y in enumerate(coordinates) if (y[0] ==pos1 and y[1] == pos2) ]
    logging.info("lay_id index = %s", res[0])
    return res[0]

###
# Get details of the next game to bet on
###
def get_next_market(market_catalogues):
    timeNow = (datetime.datetime.now(pytz.timezone("Europe/London"))-datetime.timedelta(hours=1)) ## minus 1 hr due to daylight savings maybe?
    logging.info("Time Now: %s", timeNow.strftime("%Y-%m-%d %T"))
    ## TODO Compare the list of markets - if timeNow is less than market start time (ie. market hasn't started yet), pick it. Otherwise, skip
    timeNow = timeNow.replace(tzinfo=pytz.UTC)

    myRaceID = 0
    myRaceVenue = ""
    startTime = ""
    for marketObj in market_catalogues:
        startTime = marketObj.market_start_time.replace(tzinfo=pytz.UTC)
        if timeNow < startTime:
            ## Found the race to bet
            myRaceID = marketObj.market_id # store the market id
            myRaceVenue = marketObj.event.venue.lower().replace(" ", "-") # store the venue
            logging.info("Found the market to lay: Name = %s, id = %s", myRaceVenue, myRaceID)

            break
        
    logging.info("Market Start Time: %s", startTime)
    
    ##TODO Sleep until x seconds before the start time
    return startTime, startTime-timeNow, myRaceID, myRaceVenue

###
# Get the runner in box 1 
# This is only used to verify the races from betfair and neds are identical
###
def get_runner1_name(market_catalogues):
    return market_catalogues[0].runners[0].runner_name

#########################################################
## Internal functions
#########################################################

def get_neds_odds(venueName): 
    options = Options()
    options.add_argument('--headless') # headless browser so GUI is not shown
    options.add_argument('--incognito')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('enable-features=NetworkServiceInProcess')
    options.add_argument('disable-features=NetworkService') 
    driver = webdriver.Chrome(options=options)

    # venueName = 'newcastle-bags'
    url = "https://www.neds.com.au/racing/" + venueName
    logging.info("Next Neds URL to try = %s", url)
    driver.get(url)
    time.sleep(2)
    try:
        
        elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "page-content"))
        )
    finally:
        data = elem.text
        
    ##############
    # Divide up the data into two parts (rankings and players)
    ##############
    flag_part2 = False 
    data_arr_part1 = [] 
    data_arr_part2 = []
    ## Check through the scraped text data
    for line in data.splitlines():
        if not flag_part2:
            data_arr_part1.append(str(''.join(line)))
        if(line == 'RUNNERS' or flag_part2 == True):
            flag_part2 = True
            data_arr_part2.append(str(''.join(line)))

    logging.debug(data_arr_part1)
    logging.debug("end of part1")
    logging.debug(data_arr_part2)


    ##############
    # Get the odds
    ##############
    odds = ['-1', '-1', '-1', '-1', '-1', '-1']
    for i,val in enumerate(data_arr_part2):
        if('1. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds[0] = '99'
            else:
                odds[0] = str(data_arr_part2[i+2]) #get the first value of that string

        elif('2. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds[1] = '99'
            else:
                odds[1] = str(data_arr_part2[i+2]) #get the first value of that string

        elif('3. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds[2] = '99'
            else:
                odds[2] = str(data_arr_part2[i+2]) #get the first value of that string

        elif('4. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds[3] = '99'
            else:
                odds[3] = str(data_arr_part2[i+2]) #get the first value of that string

        elif('5. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds[4] = '99'
            else:
                odds[4] = str(data_arr_part2[i+2]) #get the first value of that string

        elif('6. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds[5] = '99'
            else:
                odds[5] = str(data_arr_part2[i+2]) #get the first value of that string


    if '-1' in odds:
        logging.error("Neds api failed")

    driver.close()

    return odds

def get_odds(venueName):
    venueName_vars = [venueName+"-bags", venueName, venueName+"-am"]
    for i in venueName_vars:
        odds_arr = get_neds_odds(i)
        if('-1' not in odds_arr):
            logging.info("True Venue Name = %s", i)
            break # found it
        
        time.sleep(3)

    return odds_arr

## Write result to a csv file
def write_to_file(fname, myRaceID, betOutcome, profit, startTime):
    with open(fname, 'a+') as f:
        writer = csv.writer(f)
        ## check if the file is empty: if NO, write newline char, if YES do nothing,
        f.seek(0) # Move read cursor to the start of file
        data = f.read(1)
        if len(data) > 0:
            f.write("\n")
        else:
            writer.writerow(['Start Time', 'Race ID', 'Bet Outcome', 'Profit/Loss'])
        
        writer.writerow([startTime, myRaceID, betOutcome, profit])

## check if it's a float
def isFloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False

if __name__ == "__main__":
    venueName = 'crayford-bags'
    get_neds_odds(venueName)
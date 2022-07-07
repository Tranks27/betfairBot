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
    if(len(odds_arr) == 0): # try a second time if result is empty
        odds_arr = get_odds(venueName)
    print("odds_arr = ", odds_arr)

    ## Check if there are 6 runners
    if len(odds_arr) != 6 or '99' in odds_arr:
        print('Length of odds_arr = ' + str(len(odds_arr)))
        print("odds_arr = ", odds_arr)
        return -2

    ## Sort out the odds_arr
    sorted_odds = sorted(odds_arr,key=float)
    print("sorted_odds = ", sorted_odds)
    pos1 = odds_arr.index(sorted_odds[0]) 
    pos2 = odds_arr.index(sorted_odds[1]) 
    pos3 = odds_arr.index(sorted_odds[2]) 
    print("Forecast = " + str(pos1+1) + "-" + str(pos2+1))

    ## TODO: check only if the 2 lowest odds are similar
    if pos1 == pos2 or pos2 == pos3:
        print('Two of the 3 smallest odds are the same : pos1 = ' + str(pos1) + ',pos2 = ' + str(pos2)+ ',pos3 = ' + str(pos3))
        return -1

    ## Choose the index of the lay selection out of 30 options or less
    coordinates = []

    for x in range(6):
        for y in range(6):
            if(x != y):
                coordinates.append((x, y))

    # res = [x+1 for x,y in enumerate(coordinates) if (y[0] ==pos1 and y[1] == pos2) ]
    res = [x for x,y in enumerate(coordinates) if (y[0] ==pos1 and y[1] == pos2) ]
    print("lay_id index = ", res[0])
    return res[0]

###
# Get details of the next game to bet on
###
def get_next_market(market_catalogues):
    timeNow = (datetime.datetime.now(pytz.timezone("Europe/London"))-datetime.timedelta(hours=1)) ## minus 1 hr due to daylight savings maybe?
    print("Time Now: ", timeNow.strftime("%Y-%m-%d %T"))
    ## TODO Compare the list of markets - if timeNow is less than market start time (ie. market hasn't started yet), pick it. Otherwise, skip
    timeNow = timeNow.replace(tzinfo=pytz.UTC)

    myRaceID = 0
    myRaceVenue = ""
    for marketObj in market_catalogues:
        startTime = marketObj.market_start_time.replace(tzinfo=pytz.UTC)
        if timeNow < startTime:
            ## Found the race to bet
            myRaceID = marketObj.market_id # store the market id
            myRaceVenue = marketObj.event.venue.lower().replace(" ", "-") # store the venue
            print("Found the market to lay: Name = " + myRaceVenue + " id = " + str(myRaceID))

            break
        
    print("Market Start Time: " + str(startTime))
    
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
    driver = webdriver.Chrome(options=options)

    odds = []

    # venueName = 'newcastle-bags'
    url = "https://www.neds.com.au/racing/" + venueName
    print("Next Neds URL to try = ", url)
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
        # print(line)

    print(data_arr_part1)
    print("end of part1")
    print(data_arr_part2)


    ##############
    # Get the odds
    ##############
    for i,val in enumerate(data_arr_part2):
        if('1. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds.append('99')
            else:
                odds.append(str(data_arr_part2[i+2])) #get the first value of that string
        elif('2. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds.append('99')
            else:
                odds.append(str(data_arr_part2[i+2])) 
        elif('3. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds.append('99')
            else:
                odds.append(str(data_arr_part2[i+2])) 
        elif('4. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds.append('99')
            else:
                odds.append(str(data_arr_part2[i+2])) 
        elif('5. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds.append('99')
            else:
                odds.append(str(data_arr_part2[i+2])) 
        elif('6. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds.append('99')
            else:
                odds.append(str(data_arr_part2[i+2])) 

    # print(odds)
    if odds == []:
        print("Neds api failed")

    driver.close()

    return odds

def get_odds(venueName):
    venueName_vars = [venueName+"-bags", venueName, venueName+"-am"]
    for i in venueName_vars:
        odds_arr = get_neds_odds(i)
        if(len(odds_arr) != 0):
            print("True Venue Name = " + i)
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

if __name__ == "__main__":
    venueName = 'crayford-bags'
    get_neds_odds(venueName)
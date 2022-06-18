from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import pandas as pd

import time

###
# function from betfair tutorial
###
def process_runner_books(runner_books):
    '''
    This function processes the runner books and returns a DataFrame with the best back/lay prices + vol for each runner
    :param runner_books:
    :return:
    '''
    best_back_prices = [runner_book.ex.available_to_back[0].price
                        if runner_book.ex.available_to_back
                        else 1.01
                        for runner_book
                        in runner_books]
    best_back_sizes = [runner_book.ex.available_to_back[0].size
                       if runner_book.ex.available_to_back
                       else 1.01
                       for runner_book
                       in runner_books]

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
    scratching_datetimes = [runner_book.removal_date for runner_book in runner_books]
    adjustment_factors = [runner_book.adjustment_factor for runner_book in runner_books]

    df = pd.DataFrame({
        'Selection ID': selection_ids,
        'Best Back Price': best_back_prices,
        'Best Back Size': best_back_sizes,
        'Best Lay Price': best_lay_prices,
        'Best Lay Size': best_lay_sizes,
        'Last Price Traded': last_prices_traded,
        'Total Matched': total_matched,
        'Status': statuses,
        'Removal Date': scratching_datetimes,
        'Adjustment Factor': adjustment_factors
    })
    return df
    
def get_neds_odds(venueName): 
    options = Options()
    options.add_argument('--headless') # headless browser so GUI is not shown
    options.add_argument('--incognito')
    driver = webdriver.Chrome(options=options)

    odds = []

    # venueName = 'newcastle-bags'
    url = "https://www.neds.com.au/racing/" + venueName
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
    abdn_flag = False
    ## Check through the scraped text data
    for line in data.splitlines():
        if(line == 'Abandoned'):
            abdn_flag = True
            break

        if not flag_part2:
            data_arr_part1.append(str(''.join(line)))
        if(line == 'RUNNERS' or flag_part2 == True):
            flag_part2 = True
            data_arr_part2.append(str(''.join(line)))
        # print(line)

    # print(data_arr_part1)
    # print("end of part1")
    # print(data_arr_part2)

    # assert(abdn_flag==True) # exit if the chosen race is abandoned


    ##############
    # Get the odds
    ##############
    for i,val in enumerate(data_arr_part2):
        if('1. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds.append('-')
            else:
                odds.append(str(data_arr_part2[i+2])) #get the first value of that string
        elif('2. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds.append('-')
            else:
                odds.append(str(data_arr_part2[i+2])) 
        elif('3. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds.append('-')
            else:
                odds.append(str(data_arr_part2[i+2])) 
        elif('4. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds.append('-')
            else:
                odds.append(str(data_arr_part2[i+2])) 
        elif('5. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds.append('-')
            else:
                odds.append(str(data_arr_part2[i+2])) 
        elif('6. ' in val):
            if(data_arr_part2[i+1] == 'SCRATCHED' or data_arr_part2[i+1] == 'SCRATCHED (LATE)'):
                odds.append('-')
            else:
                odds.append(str(data_arr_part2[i+2])) 

    # print(odds)
    if odds == []:
        print("Neds api failed")
        assert()
    driver.close()

    return odds

def choose_lay_option(venueName):
    odds_arr = get_neds_odds(venueName)
    print(odds_arr)
    ## Check if there are similar odds, check if len of list and len of set are equal
    if len(odds_arr) != len(set(odds_arr)):
        return -1

    ## Check if there 6 runners
    if len(odds_arr) != 6:
        return -2

    ## Sort out the odds_arr
    sorted_odds = sorted(odds_arr,key=float)
    print(sorted_odds)
    pos1 = odds_arr.index(sorted_odds[0]) 
    pos2 = odds_arr.index(sorted_odds[1]) 
    print(str(pos1+1) + "," + str(pos2+1))

    ## Choose the index of the lay selection out of 30 options or less
    coordinates = []

    for x in range(6):
        for y in range(6):
            if(x != y):
                coordinates.append((x, y))

    # res = [x+1 for x,y in enumerate(coordinates) if (y[0] ==pos1 and y[1] == pos2) ]
    res = [x for x,y in enumerate(coordinates) if (y[0] ==pos1 and y[1] == pos2) ]
    print(res[0])
    return res[0]

if __name__ == "__main__":
    venueName = 'crayford-bags'
    get_neds_odds(venueName)
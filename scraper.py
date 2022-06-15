from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import time
import csv

options = Options()
options.add_argument('--headless') # headless browser so GUI is not shown
options.add_argument('--incognito')
driver = webdriver.Chrome(options=options)

odds = []

venueName = 'newcastle-bags'
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

print(odds)

driver.close()
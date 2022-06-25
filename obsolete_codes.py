# # pick the random venue
# import random
# random_pick = random.randint(1,len(fc_venue_ids))
# # random_pick = 1
# venueOfTheDay_name = fc_venue_names[random_pick]
# venueOfTheDay_id = fc_venue_ids[random_pick]

# venueOfTheDay_name, venueOfTheDay_id


# market_types_filter = filters.market_filter(event_ids=[venueOfTheDay_id])

# market_types = trading.betting.list_market_types(
#     filter=market_types_filter
# )

# market_types_venueOfTheDay = pd.DataFrame({
#     'Market Type': [market_type_object.market_type for market_type_object in market_types],
# })
# market_types_venueOfTheDay


####################################################################################################################
####################################################################################################################
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
# driver = webdriver.Chrome()


url = 'https://www.neds.com.au/greyhound-racing/international'
driver.get(url)
time.sleep(2)
try:
    
    elem = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "page-content"))
    )
finally:
    data = elem.text

print(data)
driver.close()


# timestr = time.strftime("%Y%m%d")
# print(timestr)

####################################################################################################################
####################################################################################################################
# cancelled_order = trading.betting.cancel_orders(market_id=myRaceID)
# # listClearedOrders
# cleared_orders = trading.betting.list_cleared_orders(bet_status="CANCELLED",
#                                                     market_ids=[myRaceID])
# # Create a DataFrame from the orders
# pd.DataFrame(cleared_orders._data['cancelledOrders'])
# cleared_orders


####################################################################################################################
## MARKET_ON_CLOSE order
####################################################################################################################
order_filter = filters.market_on_close_order(
    liability=liability_amount
)

instructions_filter = filters.place_instruction(
    selection_id = str(lay_selection_id),
    side="LAY",
    ## fixed price order
    order_type = "LIMIT",
    limit_order=order_filter

    ## flexible price order
    # order_type = "MARKET_ON_CLOSE",
    # market_on_close_order= order_filter
)
# %%
# Import libraries
import betfairlightweight
from betfairlightweight import filters
import pandas as pd
import numpy as np
import os
import datetime
import json
from utils import process_runner_books
import pytz
import time

# Project libraries
import constants

# Change this certs path to wherever you're storing your certificates
certs_path = "/home/naing/certs/"

# Change these login details to your own
my_username = constants.USERNAME
my_password = constants.PASSWORD
# my_app_key = constants.API_KEY_DEMO #demo
my_app_key = constants.API_KEY_LIVE #live

trading = betfairlightweight.APIClient(username=my_username,
                                       password=my_password,
                                       app_key=my_app_key,
                                       certs=certs_path)

trading.login()

# %%
## TODO
liability_amount = 1500

# %%
#######################################
# Filter out only greyhoud races
#######################################
gh_racing_id = constants.GH_RACING_ID #Greyhound racing ID
greyhound_racing_filter = filters.market_filter(
    event_type_ids=[gh_racing_id],
    market_countries=['GB'],
    market_type_codes=['FORECAST'],
    market_start_time={
        'to': (datetime.datetime.utcnow() + datetime.timedelta(hours=6)).strftime("%Y-%m-%dT%TZ") #sydtime 5pm to 7am next day for GB gh races
    }
)

#  This returns a list
gb_gh_events = trading.betting.list_events(
    filter=greyhound_racing_filter)

# Create a DataFrame with all the events by iterating over each event object
gb_gh_events_df = pd.DataFrame({
    'Event Name': [event_object.event.name for event_object in gb_gh_events],
    'Event ID': [event_object.event.id for event_object in gb_gh_events],
    'Event Venue': [event_object.event.venue for event_object in gb_gh_events],
    'Country Code': [event_object.event.country_code for event_object in gb_gh_events],
    'Time Zone': [event_object.event.time_zone for event_object in gb_gh_events],
    'Open Date': [event_object.event.open_date for event_object in gb_gh_events],
    'Market Count': [event_object.market_count for event_object in gb_gh_events]
})

gb_gh_events_df

# %%
#######################################
#TODO: extract a list of IDs for the forecast markets
#######################################
fc_venue_ids = []
fc_venue_names = []
for eventObj in gb_gh_events:
    fc_venue_ids.append(eventObj.event.id)
    fc_venue_names.append(eventObj.event.name)

fc_venue_ids, fc_venue_names


# %%
#######################################
## Filter out the next 5 upcoming games
#######################################
market_catalogue_filter = filters.market_filter(
    event_ids=fc_venue_ids)

market_catalogues = trading.betting.list_market_catalogue(
    filter=market_catalogue_filter,
    market_projection= ['MARKET_START_TIME', 'EVENT'],
    max_results='5',
    sort='FIRST_TO_START'
)

market_types_venueOfTheDay_df = pd.DataFrame({
    'Market Name': [market_cat_object.market_name for market_cat_object in market_catalogues],
    'Market ID': [market_cat_object.market_id for market_cat_object in market_catalogues],
    'Market Start Time': [market_cat_object.market_start_time for market_cat_object in market_catalogues],
    'Total Matched': [market_cat_object.total_matched for market_cat_object in market_catalogues],
    'Venue': [market_cat_object.event.venue for market_cat_object in market_catalogues]
    
})

market_types_venueOfTheDay_df

# %%
#######################################
## Check the start time of the next game
## and sleep until 15 seconds before the game
#######################################
timeNow = (datetime.datetime.now(pytz.timezone("Europe/London"))-datetime.timedelta(hours=1)) ## minus 1 hr due to daylight savings maybe?
print("Time Now: ")
print(timeNow.strftime("%Y-%m-%d %T"))
## TODO Compare the list of markets - if timeNow is less than market start time (ie. market hasn't started yet), pick it. Otherwise, skip
time1 = timeNow.replace(tzinfo=pytz.UTC)

for marketObj in market_catalogues:
    time2 = marketObj.market_start_time.replace(tzinfo=pytz.UTC)
    if time1 < time2:
        ## Found the race to bet
        myRaceID = marketObj.market_id # store the market id
        myRaceVenue = marketObj.event.venue.lower().replace(" ", "-") # store the venue
        print("Found the market to lay: Name = " + myRaceVenue + " id = " + str(myRaceID))
        break
print("Market Start Time: ")
print(time2)

##TODO Sleep until x seconds before the start time
time_to_sleep = (time2-time1 - datetime.timedelta(seconds=constants.PREBET_DELAY)).seconds
print("Sleeping for " + str(time_to_sleep) + " seconds")
time.sleep(time_to_sleep)
print("Sleeping done")

##TODO Choose the liability amount



# %%
# Create a price filter. Get all traded and offer data
price_filter = filters.price_projection(
    price_data=['EX_BEST_OFFERS']
)

# Request market books
market_books = trading.betting.list_market_book(
    market_ids=[myRaceID],
    price_projection=price_filter
)

# Grab the first market book from the returned list as we only requested one market 
market_book = market_books[0]

runners_df = process_runner_books(market_book.runners)

#TODO: extract a list of IDs for the lay options
lay_options_ids = []
for obj in market_book.runners:
    lay_options_ids.append(obj.selection_id)

print(lay_options_ids)

# %%
#######################################
# Get odds from NEDS
#######################################
from utils import choose_lay_option

lay_selection_index = choose_lay_option(myRaceVenue)

if(lay_selection_index == -1):
    print("ERROR!!! 2 same odds found")
    assert()
    
elif(lay_selection_index == -2):
    print("ERROR!!! less than 6 runners")
    # assert()

elif(lay_selection_index == -3):
    print("ERROR!!! NEDS API failed")
    assert()
else:
    print("Lay option found successfully")
    print(lay_selection_index)

lay_selection_id = lay_options_ids[lay_selection_index]
print(lay_selection_id)
fav_price = runners_df.loc[runners_df['Best Lay Price'].idxmin(), 'Best Lay Price'] + 1

limit_order_filter = filters.limit_order(
    price=fav_price,
    persistence_type='LAPSE',
    bet_target_type='PAYOUT',
    bet_target_size=liability_amount # use this if i want $1500 as liability
)

# market_close_order_filter = filters.market_on_close_order(
#     liability=liability_amount
# )

instructions_filter = filters.place_instruction(
    selection_id = str(lay_selection_id),
    side="LAY",
    ## fixed price order
    order_type = "LIMIT",
    limit_order=limit_order_filter

    ## flexible price order
    # order_type = "MARKET_ON_CLOSE",
    # market_on_close_order= market_close_order_filter
)

instructions_filter

# %%
order = trading.betting.place_orders(
    market_id = myRaceID,
    customer_strategy_ref='Naing_maker',
    instructions=[instructions_filter]
)

# %%
# listClearedOrders
# cleared_orders = trading.betting.list_cleared_orders(bet_status="SETTLED",
#                                                     market_ids=[myRaceID])

# # 
# # Create a DataFrame from the orders
# pd.DataFrame(cleared_orders._data['clearedOrders'])

# %%



